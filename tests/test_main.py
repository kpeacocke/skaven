import sys
import threading
import pytest
from typing import Dict, Callable, Optional, Tuple, Any
from displayboard import sounds, lighting, video_loop
import displayboard.main as dispatcher
from unittest.mock import MagicMock
import os
import subprocess
import argparse


class FakeThread:
    """
    A fake Thread to capture target and name, without starting real threads.
    """

    instances: list["FakeThread"] = []

    def __init__(
        self,
        target: Optional[Callable[..., None]] = None,
        name: Optional[str] = None,
        daemon: Optional[bool] = None,
        args: Tuple[Any, ...] = (),
        **kwargs: object
    ) -> None:
        self.target = target
        self.name = name
        self.daemon = daemon
        self.args = args
        FakeThread.instances.append(self)

    def start(self) -> None:
        if callable(self.target):
            try:
                if self.args:
                    self.target(*self.args)
                else:
                    self.target()
            except KeyboardInterrupt:
                pass


@pytest.fixture(autouse=True)
def patch_threads_and_calls(monkeypatch: pytest.MonkeyPatch) -> Dict[str, int]:
    FakeThread.instances.clear()
    monkeypatch.setattr(threading, "Thread", FakeThread)
    calls = {"sounds": 0, "lighting": 0, "video": 0}
    monkeypatch.setattr(
        sounds, "main", lambda stop_event=None: calls.update(sounds=calls["sounds"] + 1)
    )
    monkeypatch.setattr(
        lighting,
        "flicker_breathe",
        lambda stop_event=None: calls.update(lighting=calls["lighting"] + 1),
    )
    monkeypatch.setattr(
        video_loop,
        "main",
        lambda stop_event=None: calls.update(video=calls["video"] + 1),
    )
    # Do NOT patch time.sleep globally here. Patch only in tests that need it.
    return calls


def test_main_join_threads_attribute_and_runtime() -> None:
    """Covers _join_threads AttributeError and RuntimeError branches."""
    mock_logger = MagicMock()

    class NoJoin(threading.Thread):
        def __init__(self) -> None:
            super().__init__()
            self.name = "NoJoinThread"

    class BadJoin(threading.Thread):
        def __init__(self) -> None:
            super().__init__()
            self.name = "BadJoinThread"

        def join(self, timeout: Optional[float] = None) -> None:
            raise RuntimeError("fail")

    dispatcher._join_threads([NoJoin(), BadJoin()], mock_logger)


def test_main_keyboard_interrupt_in_video(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Covers KeyboardInterrupt in handle_video_playback."""
    monkeypatch.setattr(sys, "argv", ["displayboard"])

    def fake_video_main(stop_event: object = None) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(dispatcher.video_loop, "main", fake_video_main)
    monkeypatch.setattr(
        dispatcher,
        "_join_threads",
        lambda threads, logger: None,
    )
    monkeypatch.setattr(
        dispatcher,
        "start_threads",
        lambda args, stop_event: [],
    )
    mock_logger = MagicMock()
    monkeypatch.setattr(
        dispatcher,
        "configure_logging",
        lambda args: mock_logger,
    )
    dispatcher.main()


def test_main_keyboard_interrupt_in_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Covers KeyboardInterrupt in handle_shutdown."""
    monkeypatch.setattr(sys, "argv", ["displayboard"])

    def fake_video_main(stop_event: object = None) -> None:
        pass

    monkeypatch.setattr(dispatcher.video_loop, "main", fake_video_main)
    monkeypatch.setattr(dispatcher, "_join_threads", lambda threads, logger: None)
    monkeypatch.setattr(dispatcher, "start_threads", lambda args, stop_event: [])
    mock_logger = MagicMock()
    monkeypatch.setattr(dispatcher, "configure_logging", lambda args: mock_logger)

    def fake_handle_video_playback(args: object, stop_event: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(dispatcher, "handle_video_playback", fake_handle_video_playback)

    def fake_video_main_shutdown(stop_event: object = None) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(dispatcher.video_loop, "main", fake_video_main_shutdown)
    dispatcher.main()


def test_main_normal_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers normal exit from main."""
    monkeypatch.setattr(
        sys, "argv", ["displayboard", "--no-sounds", "--no-lighting", "--no-video"]
    )
    monkeypatch.setattr(dispatcher, "start_threads", lambda args, stop_event: [])
    monkeypatch.setattr(dispatcher, "configure_logging", lambda args: None)
    # Bypass video playback loop entirely for normal exit
    monkeypatch.setattr(
        dispatcher, "handle_video_playback", lambda args, stop_event: None
    )
    dispatcher.main()


def test_parse_args_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure default parse_args has all flags False."""
    monkeypatch.setattr(sys, "argv", ["displayboard"])
    args = dispatcher.parse_args()
    assert not args.no_sounds
    assert not args.no_video
    assert not args.no_lighting
    assert not args.no_bell


def test_configure_logging_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers configure_logging with debug flag (line 144)."""
    import argparse
    import logging

    args = argparse.Namespace(debug=True, verbose=False)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logger = dispatcher.configure_logging(args)
    config = getattr(dispatcher, "config")
    assert logger.getEffectiveLevel() == config.LOG_LEVEL_VERBOSE


def test_configure_logging_verbose(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers configure_logging with verbose flag (line 146)."""
    import argparse
    import logging

    args = argparse.Namespace(debug=False, verbose=True)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logger = dispatcher.configure_logging(args)
    config = getattr(dispatcher, "config")
    assert logger.getEffectiveLevel() == config.LOG_LEVEL_DEFAULT


def test_handle_video_playback_exit_branch() -> None:
    """Covers handle_video_playback loop exit branch (121->exit)."""

    # This test is now covered by test_handle_shutdown_branches using dummy_event
    pass


def test_handle_shutdown_exit_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers handle_shutdown loop exit branch (146-148)."""

    # This test is now covered by test_handle_shutdown_branches using dummy_event
    pass


def test_handle_shutdown_branches(
    monkeypatch: pytest.MonkeyPatch,
    dummy_event: threading.Event,
) -> None:
    """Covers handle_shutdown loop exit and wait branches using dummy_event."""
    # Use real parse_args for coverage
    # Patch sys.argv to only include arguments that parse_args expects
    monkeypatch.setattr(sys, "argv", ["displayboard"])
    args = dispatcher.parse_args()
    mock_logger = MagicMock()
    monkeypatch.setattr(dispatcher, "_join_threads", lambda threads, logger: None)

    # Exit branch: event is set before entering
    dummy_event.set()
    dispatcher.handle_shutdown([], dummy_event, mock_logger, args)

    # Wait branch: event is not set, will set after one wait
    dummy_event.clear()
    call_count = {"wait": 0}

    # Force the no_video branch so stop_event.wait is called
    args.no_video = True

    def fake_wait(timeout: Optional[float] = None) -> bool:
        call_count["wait"] += 1
        dummy_event.set()  # Exit after one call
        return True

    dummy_event.wait = fake_wait  # type: ignore
    dispatcher.handle_shutdown([], dummy_event, mock_logger, args)
    assert call_count["wait"] == 1


def test_join_threads_attributeerror(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests _join_threads except AttributeError branch."""
    mock_logger = MagicMock()

    class NoJoinObj(threading.Thread):
        def __init__(self) -> None:
            super().__init__()
            self.name = "NoJoinObj"

    dispatcher._join_threads([NoJoinObj()], mock_logger)


def test_configure_logging_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Tests configure_logging default path (logging.basicConfig).
    """
    import argparse
    import logging

    args = argparse.Namespace(debug=False, verbose=False)
    # Remove all handlers to avoid duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logger = dispatcher.configure_logging(args)
    from displayboard import config

    assert logger.getEffectiveLevel() == config.LOG_LEVEL_WARNING


def test_configure_logging_sets_handlers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Tests configure_logging when no handlers exist, ensuring logging.basicConfig is called.
    """
    import argparse
    import logging

    args: argparse.Namespace = argparse.Namespace(debug=False, verbose=False)
    # Remove all handlers to ensure basicConfig is called
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    # Patch logging.basicConfig to track call
    called: dict[str, Any] = {}
    orig_basicConfig = logging.basicConfig

    def fake_basicConfig(*a: Any, **kwargs: Any) -> None:
        called["basicConfig"] = True
        return orig_basicConfig(*a, **kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_basicConfig)
    dispatcher.configure_logging(args)
    assert called.get("basicConfig")


def test_configure_logging_real_basicconfig() -> None:
    """
    Tests configure_logging real call to logging.basicConfig.
    """
    import argparse
    import logging

    args = argparse.Namespace(debug=False, verbose=False)
    # Remove all handlers to ensure basicConfig is called
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logger = dispatcher.configure_logging(args)
    config = getattr(dispatcher, "config")
    assert logger.getEffectiveLevel() == config.LOG_LEVEL_WARNING


def test_join_threads_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests _join_threads normal debug branch (logger.debug)."""
    mock_logger = MagicMock()
    # Set logger.debug to a real function to check call
    calls = {}

    def fake_debug(msg: str) -> None:
        calls["debug"] = msg

    mock_logger.debug.side_effect = fake_debug

    class GoodJoinObj(threading.Thread):
        def __init__(self) -> None:
            super().__init__()
            self.name = "GoodJoinObj"

        def join(self, timeout: Optional[float] = None) -> None:
            pass

    good_join_obj: threading.Thread = GoodJoinObj()
    dispatcher._join_threads([good_join_obj], mock_logger)


def test_handle_shutdown_video_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers handle_shutdown branch where video is enabled (calls video_loop.main)."""
    import argparse
    import threading
    import displayboard.main as main
    import logging

    called = {}

    def dummy_video_main(stop_event: Optional[threading.Event] = None) -> None:
        called["video"] = True

    monkeypatch.setattr(main.video_loop, "main", dummy_video_main)
    args = argparse.Namespace(no_video=False)
    threads: list[threading.Thread] = []
    stop_event = threading.Event()
    main.handle_shutdown(
        threads, stop_event, logging.getLogger("displayboard.test"), args
    )
    assert called["video"]


def test_handle_video_playback_keyboardinterrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Covers KeyboardInterrupt in handle_video_playback (video enabled)."""
    import argparse
    import threading
    import displayboard.main as main

    args = argparse.Namespace(no_video=False)
    stop_event = threading.Event()

    def raise_keyboardinterrupt(stop_event: object = None) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(main.video_loop, "main", raise_keyboardinterrupt)
    # Should not raise, just handle KeyboardInterrupt
    main.handle_video_playback(args, stop_event)


def test_handle_shutdown_keyboardinterrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers KeyboardInterrupt in handle_shutdown (video enabled)."""
    import argparse
    import threading
    import displayboard.main as main
    import logging

    args = argparse.Namespace(no_video=False)
    stop_event = threading.Event()

    def raise_keyboardinterrupt(stop_event: object = None) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(main.video_loop, "main", raise_keyboardinterrupt)
    # Should not raise, just handle KeyboardInterrupt
    main.handle_shutdown([], stop_event, logging.getLogger("displayboard.test"), args)


def test_main_py_entry_subprocess() -> None:
    """Covers the __main__ block in displayboard.main using subprocess."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "displayboard.main",
            "--no-sounds",
            "--no-video",
            "--no-lighting",
            "--test-exit",
        ],
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0


@pytest.mark.parametrize(
    "no_sounds,no_lighting,no_bell,expected_sounds,expected_lighting,expected_bell,expected_len",
    [
        (False, False, False, 1, 1, 1, 3),
        (True, False, False, 0, 1, 1, 2),
        (False, True, False, 1, 0, 1, 2),
        (True, True, False, 0, 0, 1, 1),
        (False, False, True, 1, 1, 0, 2),
        (True, False, True, 0, 1, 0, 1),
        (False, True, True, 1, 0, 0, 1),
        (True, True, True, 0, 0, 0, 0),
    ],
)
def test_start_threads_calls(
    patch_threads_and_calls: dict[str, Any],
    no_sounds: bool,
    no_lighting: bool,
    no_bell: bool,
    expected_sounds: int,
    expected_lighting: int,
    expected_bell: int,
    expected_len: int,
) -> None:
    """Covers start_threads enabling/disabling sound, lighting, and bell threads."""
    # Patch bell.main to increment a counter
    import displayboard.bell

    bell_calls = {"bell": 0}
    orig_bell_main = displayboard.bell.main

    def fake_bell_main(stop_event: Optional[Any] = None) -> None:
        bell_calls["bell"] += 1

    displayboard.bell.main = fake_bell_main

    args = argparse.Namespace(
        no_sounds=no_sounds, no_lighting=no_lighting, no_bell=no_bell
    )
    stop_event = threading.Event()
    threads = dispatcher.start_threads(args, stop_event)
    assert len(threads) == expected_len
    assert patch_threads_and_calls["sounds"] == expected_sounds
    assert patch_threads_and_calls["lighting"] == expected_lighting
    assert bell_calls["bell"] == expected_bell
    displayboard.bell.main = orig_bell_main


@pytest.mark.timeout(2)
def test_handle_video_playback_no_video_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    import time

    args = argparse.Namespace(no_video=True)
    stop_event = threading.Event()
    stop_event.set()
    # Defensive: patch time.sleep to avoid any possible hang
    monkeypatch.setattr(time, "sleep", lambda s: None)
    dispatcher.handle_video_playback(args, stop_event)


@pytest.mark.timeout(2)
def test_handle_video_playback_no_video_keyboardinterrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Covers KeyboardInterrupt in disabled video playback loop."""

    args = argparse.Namespace(no_video=True)
    stop_event = threading.Event()
    call = {"sleep": 0}

    def fake_sleep(interval: float) -> None:
        call["sleep"] += 1
        raise KeyboardInterrupt

    import time

    # Patch the sleep function in the time module directly
    monkeypatch.setattr(time, "sleep", fake_sleep)
    dispatcher.handle_video_playback(args, stop_event)
    assert call["sleep"] == 1


# Remove duplicate test_handle_video_playback_video_enabled if present


def test_handle_video_playback_video_enabled(
    patch_threads_and_calls: dict[str, int],
) -> None:
    """Covers normal handle_video_playback when video is enabled without errors."""
    args = argparse.Namespace(no_video=False)
    stop_event = threading.Event()
    dispatcher.handle_video_playback(args, stop_event)
    assert patch_threads_and_calls["video"] == 1
