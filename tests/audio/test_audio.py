from muxtools import ensure_path, Setup, get_workdir, ParsedFile, do_audio, get_executable, Opus, Sox, FFMpeg, resolve_timesource_and_scale, VideoMeta
from muxtools.utils.env import communicate_stdout
from time import sleep
from shutil import rmtree, copy
import pytest
import logging
import os

test_dir = ensure_path(__file__, None).parent.parent
sample_file_aac = test_dir / "test-data" / "audio" / "aac_source.m4a"
sample_file_flac = test_dir / "test-data" / "audio" / "flac_source.flac"
sample_file_wav = test_dir / "test-data" / "audio" / "wav_source.wav"
sample_file_wav_fake24 = test_dir / "test-data" / "audio" / "wav_source_fake24.wav"


def get_md5_for_stream(file) -> str:
    ffmpeg = get_executable("ffmpeg")
    args = [ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(file), "-map", "0:a:0", "-f", "md5", "-"]
    code, out = communicate_stdout(args)
    if code != 0:
        raise RuntimeError(f"Failed to get md5 for stream in file: {str(file)}")
    return out.split("=")[1]


@pytest.fixture(autouse=True)
def setup_and_remove():
    Setup("Test", None)

    yield

    sleep(0.1)
    # rmtree(get_workdir())


def test_lossy_input_no_encode():
    out = do_audio(sample_file_aac)
    logging.getLogger("test_lossy_input_no_encode").log(200, get_md5_for_stream(out.file))


def test_lossy_input(caplog):
    out = do_audio(sample_file_aac, encoder=Opus())

    # Prints a danger log for reencoding lossy audio
    assert len([record for record in caplog.get_records("call") if record.levelname == "DANGER"]) == 1

    logging.getLogger("test_lossy_input").log(200, get_md5_for_stream(out.file))


def test_flac_input():
    out = do_audio(sample_file_flac, encoder=Opus())
    logging.getLogger("test_flac_input").log(200, get_md5_for_stream(out.file))


def test_flac_sox_trim():
    # Cba to add sox to the github workflow
    if os.name != "nt":
        return
    meta = VideoMeta.from_json(test_dir / "test-data" / "input" / "vigilantes_s01e01.json")

    out = do_audio(sample_file_flac, trims=(-24, None), num_frames=len(meta.pts), timesource=meta, trimmer=Sox(), encoder=Opus())
    logging.getLogger("test_flac_sox_trim").log(200, get_md5_for_stream(out.file))


def test_flac_ffmpeg_trim():
    # Cba to add sox to the github workflow
    if os.name != "nt":
        return
    meta = VideoMeta.from_json(test_dir / "test-data" / "input" / "vigilantes_s01e01.json")

    out = do_audio(sample_file_flac, trims=(24, None), timesource=meta, trimmer=FFMpeg.Trimmer(), encoder=Opus())
    logging.getLogger("test_flac_ffmpeg_trim").log(200, get_md5_for_stream(out.file))
