import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bot import lark_test_bot as bot


MOTOR9_TRIGGER = """
2026-08-03 11:44:19.714 W/ethercat(mroslaunch)(627/627): motor9 something happened, statusword 0x1208 code 0x0
2026-08-03 11:44:19.726 E/ethercat(mroslaunch)(627/627): Motor = 65535, 0xf10b, Too many loss.
2026-08-03 11:44:19.753 I/ethercat(mroslaunch)(627/627): [88] 'EtherCAT error rx frames of port0': 255
2026-08-03 11:44:19.754 I/ethercat(mroslaunch)(627/627): [90] 'EtherCAT lost link cnt of port1': 0
2026-08-03 11:44:37.094 I/ethercat(mroslaunch)(1058/1058): Motor 9 (slave 11) enabled successfully.
""".strip()

MOTOR5_RECOVERY_FAILURE = """
2026-08-03 11:32:36.706 W/ethercat(mroslaunch)(635/635): motor9 something happened, statusword 0x1208 code 0x0
2026-08-03 11:32:36.712 E/ethercat(mroslaunch)(635/635): Motor = 65535, 0xf10b, Too many loss.
2026-08-03 11:32:53.892 E/ethercat(mroslaunch)(1058/1058): Failed to enable motor 5 (slave 6) statusword 0x12a1 code 0x7121
2026-08-03 11:33:11.014 E/ethercat(mroslaunch)(1058/1058): Failed to enable motor 5 (slave 6) statusword 0x12a1 code 0x7121
""".strip()

MOTOR10_RECOVERY_FAILURE = """
2026-08-01 10:01:37.733 W/ethercat(mroslaunch)(640/640): motor9 something happened, statusword 0x1208 code 0x0
2026-08-01 10:01:37.740 E/ethercat(mroslaunch)(640/640): Motor = 65535, 0xf10b, Too many loss.
2026-08-01 10:01:55.221 E/ethercat(mroslaunch)(1058/1058): Failed to enable motor 10 (slave 12) statusword 0x12a1 code 0x7121
2026-08-01 10:02:12.400 E/ethercat(mroslaunch)(1058/1058): Failed to enable motor 10 (slave 12) statusword 0x12a1 code 0x7121
""".strip()

ALL_MOTORS_LINK_DROP = "\n".join(
    [
        *[
            f"2026-07-31 10:21:01.792 W/ethercat(mroslaunch)(635/635): "
            f"motor{motor} something happened, statusword 0x0 code 0xf"
            for motor in range(1, 11)
        ],
        "2026-07-31 10:21:01.802 E/ethercat(mroslaunch)(635/635): Motor = 65535, 0xf10b, Too many loss.",
        "2026-07-31 10:21:15.831 I/ethercat(mroslaunch)(635/635): [8a] 'EtherCAT error rx frames of port1': 255",
        "2026-07-31 10:21:15.831 I/ethercat(mroslaunch)(635/635): [90] 'EtherCAT lost link cnt of port1': 1",
        "2026-07-31 10:21:15.832 I/ethercat(mroslaunch)(635/635): [92] 'EtherCAT lost link cnt of port3': 1",
    ]
)


class EvidenceGateRegressionTests(unittest.TestCase):
    def test_motor9_trigger_and_recovery_pass(self):
        answer = (
            "电机9（motor9/slave11）出现 statusword 0x1208 code 0x0，"
            "随后直接触发 Too many loss；帧错误非零，lost link 为0，主站重启后恢复。"
        )
        bot.validate_log_analysis_answer(MOTOR9_TRIGGER, answer)

    def test_motor9_trigger_cannot_be_reclassified_as_manual_power(self):
        answer = (
            "电机9 statusword 0x1208 code 0x0，"
            "最终根因为遥控器手动掉电并在主站重启后恢复。"
        )
        with self.assertRaisesRegex(RuntimeError, "不得改判为遥控器"):
            bot.validate_log_analysis_answer(MOTOR9_TRIGGER, answer)

    def test_motor5_recovery_failure_pass(self):
        answer = (
            "初始触发为电机9 statusword 0x1208 code 0x0 后出现 Too many loss；"
            "后续未恢复原因为电机5 statusword 0x12a1 code 0x7121 堵转保护。"
        )
        bot.validate_log_analysis_answer(MOTOR5_RECOVERY_FAILURE, answer)

    def test_motor10_recovery_failure_pass(self):
        answer = (
            "初始触发为电机9 statusword 0x1208 code 0x0 后出现 Too many loss；"
            "后续未恢复原因为电机10 statusword 0x12a1 code 0x7121 堵转保护。"
        )
        bot.validate_log_analysis_answer(MOTOR10_RECOVERY_FAILURE, answer)

    def test_motor_range_and_nonzero_lost_link_pass(self):
        answer = (
            "motor1~10 全部出现 statusword 0x0 code 0xf，随后 Too many loss；"
            "[90]/[92] lost link 非零，属于硬件链路瞬断，不能判为遥控器掉电。"
        )
        bot.validate_log_analysis_answer(ALL_MOTORS_LINK_DROP, answer)

    def test_nonzero_lost_link_rejects_all_zero_claim(self):
        answer = (
            "motor1~10 全部出现 statusword 0x0 code 0xf；"
            "所有 lost link 计数均为0。"
        )
        with self.assertRaisesRegex(RuntimeError, "存在非零 lost link"):
            bot.validate_log_analysis_answer(ALL_MOTORS_LINK_DROP, answer)


class PreprocessingRegressionTests(unittest.TestCase):
    def test_deep_analysis_keeps_evidence_without_embedding_knowledge_base(self):
        log = "\n".join(
            [
                "2026-08-03 11:44:19.714 W/ethercat(mroslaunch)(1/1): motor9 something happened, statusword 0x1208 code 0x0",
                "2026-08-03 11:44:19.726 E/ethercat(mroslaunch)(1/1): Motor = 65535, 0xf10b, Too many loss.",
                "2026-08-03 11:44:19.727 I/snowball(mroslaunch)(2/2): >>>diag ecm level:2 code:-1 msg:Too many loss.",
                "2026-08-03 11:44:19.727 E/snowball(mroslaunch)(2/2): >>>>>ecm exp",
                "2026-08-03 11:44:19.727 E/snowball(mroslaunch)(2/2): >>>>>|ecm err|",
                "2026-08-03 11:44:31.184 I/ethercat(mroslaunch)(3/3): Found 12 slaves.",
                "2026-08-03 11:44:37.094 I/ethercat(mroslaunch)(3/3): Motor 9 (slave 11) enabled successfully.",
                "2026-08-03 11:44:37.170 I/snowball(mroslaunch)(4/4): >>>diag ecm level:0 code:0 msg:ethercat ok!",
            ]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.log.active"
            path.write_text(log, encoding="utf-8")
            source = bot.prepare_log_analysis_source(path)

        self.assertIn("motor9 something happened", source)
        self.assertIn("Motor 9 (slave 11) enabled successfully", source)
        self.assertNotIn("# EtherCAT 主站异常诊断知识库", source)
        self.assertNotIn("EtherCAT 主站异常判断依据（知识库", source)


class CorrectionLoopRegressionTests(unittest.TestCase):
    class FakeProcess:
        def __init__(self, answer):
            self.answer = answer
            self.returncode = 0

        def communicate(self, timeout=None):
            return self.answer, ""

    def test_revision_reuses_session_and_sends_only_gate_error(self):
        calls = []
        answers = iter(["incomplete answer", "corrected answer"])

        def fake_popen(args, **kwargs):
            calls.append(args)
            return self.FakeProcess(next(answers))

        def fake_validate(_source, answer):
            if answer == "incomplete answer":
                raise RuntimeError("missing motor9")

        patches = (
            patch.object(bot, "start_ai_usage"),
            patch.object(bot, "finish_ai_usage"),
            patch.object(bot, "is_cancel_requested", return_value=False),
            patch.object(bot, "prepare_log_analysis_source", return_value="evidence"),
            patch.object(bot, "build_prompt", return_value="FULL ORIGINAL PROMPT"),
            patch.object(bot, "set_job_progress"),
            patch.object(bot, "safe_update_job_card"),
            patch.object(bot, "validate_log_analysis_answer", side_effect=fake_validate),
            patch.object(bot.subprocess, "Popen", side_effect=fake_popen),
            patch.object(bot, "LOG_ANALYSIS_MAX_REVISIONS", 2),
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], \
                patches[6], patches[7], patches[8], patches[9]:
            result = bot.run_copilot(
                {"job_id": "job-test", "action": "log_analysis", "source": "x"},
                bot.ROOT,
            )

        self.assertEqual("corrected answer", result)
        self.assertEqual(2, len(calls))
        session_id = calls[0][calls[0].index("--session-id") + 1]
        self.assertIn(f"--resume={session_id}", calls[1])
        revision_prompt = calls[1][calls[1].index("-p") + 1]
        self.assertIn("missing motor9", revision_prompt)
        self.assertNotIn("FULL ORIGINAL PROMPT", revision_prompt)
        self.assertNotIn("incomplete answer", revision_prompt)


if __name__ == "__main__":
    unittest.main()
