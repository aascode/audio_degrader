import os
import shutil
import librosa as lr
import numpy as np
import logging
from audio_degrader import Degradation, DegradationUsageDocGenerator
from audio_degrader import DegradationTrim, DegradedAudioFile
from audio_degrader import DegradationMp3, DegradationGain, DegradationMix
from audio_degrader import DegradationResample, DegradationConvolution

TEST_STEREO_WAV_PATH = './tests/test_files/test30s_44100_stereo_pcm16le.wav'
TEST_MONO_WAV_PATH = './tests/test_files/test30s_44100_mono_pcm16le.wav'
TEST_MONO_8K_WAV_PATH = './tests/test_files/test30s_8000_mono_pcm16le.wav'
TMP_PATH = './tests/tmp'


class TestDegradationTrim:

    def setup_class(self):
        logging.basicConfig(level=logging.DEBUG)
        if not os.path.isdir(TMP_PATH):
            os.makedirs(TMP_PATH)
        self.daf = DegradedAudioFile(TEST_STEREO_WAV_PATH,
                                     TMP_PATH)

    def test_degradation_trim(self):
        samples, sample_rate = lr.core.load(self.daf.tmp_path,
                                            sr=None, mono=False)
        prev_length = samples.shape[1]
        degradation_trim = DegradationTrim()
        trim_seconds = 1
        degradation_trim.set_parameters_values({'start_time': trim_seconds})
        self.daf.apply_degradation(degradation_trim)
        samples, sample_rate = lr.core.load(self.daf.tmp_path,
                                            sr=None, mono=False)
        after_length = samples.shape[1]
        assert after_length == prev_length - int(sample_rate * trim_seconds)

    def teardown_class(self):
        shutil.rmtree(TMP_PATH)


class TestDegradationMp3:

    def setup_class(self):
        logging.basicConfig(level=logging.DEBUG)
        if not os.path.isdir(TMP_PATH):
            os.makedirs(TMP_PATH)
        self.daf = DegradedAudioFile(TEST_STEREO_WAV_PATH,
                                     TMP_PATH)

    def test_degradation_mp3(self):
        degradation_mp3 = DegradationMp3()
        bitrate = '16k'
        degradation_mp3.set_parameters_values({'bitrate': bitrate})
        self.daf.apply_degradation(degradation_mp3)

    def teardown_class(self):
        shutil.rmtree(TMP_PATH)


class TestDegradationGain:

    def setup_class(self):
        logging.basicConfig(level=logging.DEBUG)
        if not os.path.isdir(TMP_PATH):
            os.makedirs(TMP_PATH)
        self.daf = DegradedAudioFile(TEST_STEREO_WAV_PATH,
                                     TMP_PATH)

    def test_degradation_gain(self):
        degradation_gain = DegradationGain()
        value = -6
        degradation_gain.set_parameters_values({'value': value})
        sum_before = np.sum(np.abs(self.daf.samples))
        self.daf.apply_degradation(degradation_gain)
        sum_after = np.sum(np.abs(self.daf.samples))
        assert (np.abs(sum_after / sum_before - 10**(value/20.0)) < 0.001)

    def teardown_class(self):
        shutil.rmtree(TMP_PATH)


class TestDegradationMix:

    def setup_class(self):
        logging.basicConfig(level=logging.DEBUG)
        if not os.path.isdir(TMP_PATH):
            os.makedirs(TMP_PATH)
        self.daf = DegradedAudioFile(TEST_STEREO_WAV_PATH,
                                     TMP_PATH)
        self.noise_path = './tests/test_files/helen.wav'

    def test_degradation_mix(self):
        degradation_mix = DegradationMix()
        degradation_mix.set_parameters_values(
            {'noise': self.noise_path,
             'snr': -12})
        self.daf.apply_degradation(degradation_mix)
        target_y, _ = lr.core.load('./tests/test_files/target_degr_mix.wav',
                                   sr=None, mono=False)
        assert np.mean(np.abs(target_y - self.daf.samples)) < 0.0001

    def teardown_class(self):
        shutil.rmtree(TMP_PATH)


class TestDegradationResample:

    def setup_class(self):
        logging.basicConfig(level=logging.DEBUG)
        if not os.path.isdir(TMP_PATH):
            os.makedirs(TMP_PATH)
        self.daf = DegradedAudioFile(TEST_STEREO_WAV_PATH,
                                     TMP_PATH)

    def test_degradation_resample(self):
        degradation_resample = DegradationResample()
        degradation_resample.set_parameters_values(
            {'sample_rate': 8000})
        self.daf.apply_degradation(degradation_resample)
        target_y, sr = lr.core.load(
            './tests/test_files/target_degr_resample.wav',
            sr=None, mono=False)
        assert self.daf.sample_rate == sr
        assert np.mean(np.abs(target_y - self.daf.samples)) < 0.001

    def teardown_class(self):
        shutil.rmtree(TMP_PATH)


class TestDegradationConvolution:

    def setup_class(self):
        logging.basicConfig(level=logging.DEBUG)
        if not os.path.isdir(TMP_PATH):
            os.makedirs(TMP_PATH)
        self.daf = DegradedAudioFile(TEST_STEREO_WAV_PATH,
                                     TMP_PATH)

    def test_degradation_convolution(self):
        degradation_convolution = DegradationConvolution()
        degradation_convolution.set_parameters_values(
            {'impulse_response': 'impulse_responses/ir_classroom_mono.wav',
             'level': '0.7'})
        self.daf.apply_degradation(degradation_convolution)
        target_y, sr = lr.core.load(
            './tests/test_files/target_degr_convolution.wav',
            sr=None, mono=False)
        assert self.daf.sample_rate == sr
        assert np.mean(np.abs(target_y - self.daf.samples)) < 0.001

    def teardown_class(self):
        shutil.rmtree(TMP_PATH)


class TestDegradationUsageDocGenerator:

    def test_degradation_help(self):

        class DegrTest(Degradation):
            name = "testdeg"
            description = "Degradation for this test"
            parameters_info = [("param1", 2.0, "Parameter one [dBs]"),
                               ("param2", 3.0, "Parameter two [seconds]")]
        degradation_trim_help = (
            DegradationUsageDocGenerator.get_degradation_help(DegrTest))
        target_docstring = '\n'.join((
            "    testdeg,param1//param2: Degradation for this test",
            "        parameters:",
            "            param1: Parameter one [dBs]",
            "            param2: Parameter two [seconds]",
            "        example:",
            "            testdeg,2.0//3.0"))
        logging.debug("\n" + degradation_trim_help)
        logging.debug(target_docstring)
        assert degradation_trim_help == target_docstring
