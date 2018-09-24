# Add to path
import sys, os

CURRENT_TEST_DIR = os.path.dirname(os.path.realpath(__file__))

sys.path.append(CURRENT_TEST_DIR + "/../src")

from data_reader import DataReader, SlayerParams
import csv
import operator
import unittest
import numpy as np
# Parameters for NMNIST
net_params = SlayerParams()
net_params.t_start = 0
net_params.t_end = 350
net_params.t_res = 1
net_params.time_unit = 1000 # How many units in one t_res (i.e. 1000 if we sample in microseconds but simulate at millisecond steps)
net_params.input_x = 34
net_params.input_y = 34
net_params.input_channels = 2

def matlab_equal_to_python_event(matlab_event, python_event):
	# Cast to avoid type problems
	matlab_event = [int(e) for e in matlab_event]
	python_event = [int(e) for e in python_event]
	# Matlab is 1 indexed, Python is 0 indexed
	return ((matlab_event[0] == (python_event[0] + 1)) and (matlab_event[1] == (python_event[1] + 1)) and
		(matlab_event[2] == (python_event[2] + 1)) and (matlab_event[3] == (python_event[3])))
 
def binned_file_comparator(matlab_bin_line, python_bin_line):
	for (matlab_entry, python_entry) in zip(matlab_bin_line, python_bin_line):
		if int(matlab_entry) != int(python_entry):
			return False
	return True

# Utility function to compare ndarray to one contained in CSV file generated separately (i.e. MATLAB)
def is_array_equal_to_file(array, filepath, has_header=False, compare_function=operator.eq):
	with open(CURRENT_TEST_DIR + filepath, 'r') as csvfile:
		reader = csv.reader(csvfile)
		# Skip header
		if has_header: next(reader, None)
		for (g_truth, read_r) in zip(reader, array):
			if not compare_function(g_truth, read_r):
				return False
	return True

class TestDataReaderFolders(unittest.TestCase):

	def test_open_nonexisting_folder(self):
		self.assertRaises(FileNotFoundError, DataReader, "nonexisting_folder", net_params)

	def test_open_valid_folder(self):
		try:
			reader = DataReader(CURRENT_TEST_DIR + "/test_files/input_data", net_params)
		except FileNotFoundError:
			self.fail("Valid input folder not found")

	def test_number_of_files_invalid_folder(self):
		# Should return 0 files valid
		reader = DataReader(CURRENT_TEST_DIR + "/test_files/input_validate", net_params)
		self.assertEqual(len(reader.input_files), 0)

	def test_input_files_ordering(self):
		file_folder = CURRENT_TEST_DIR + "/test_files/input_data/"
		reader = DataReader(file_folder, net_params)
		self.assertEqual(reader.input_files[0], file_folder + '1.bs2')

	def test_init_invalid_network_params(self):
		invalid_params = SlayerParams()
		self.assertRaises(ValueError, DataReader, CURRENT_TEST_DIR + "/test_files/input_data", invalid_params)


class TestDataReaderFunc(unittest.TestCase):

	def setUp(self):
		self.reader = DataReader(CURRENT_TEST_DIR + "/test_files/input_data", net_params)

	def test_number_of_files_valid_folder(self):
		self.assertEqual(len(self.reader.input_files), 2)

	def test_read_invalid_input_file(self):
		self.assertRaises(FileNotFoundError, self.reader.read_file, "nonexisting_file.garbage")

	def test_process_event(self):
		# Actually first line of test file
		raw_bytes = bytes.fromhex('121080037d')
		# Everything is zero indexed in python, except time
		event = (19,17,2,893)
		self.assertTrue(matlab_equal_to_python_event(event, self.reader.process_event(raw_bytes)))

	# Check proper I/O
	def test_read_input_file(self):
		ev_array = self.reader.read_file(self.reader.input_files[0])
		self.assertTrue(is_array_equal_to_file(ev_array, "/test_files/input_validate/1_raw_spikes.csv", has_header=True, compare_function=matlab_equal_to_python_event))

	def test_spikes_binning(self):
		ev_array = self.reader.read_file(self.reader.input_files[0])
		binned_spikes = self.reader.bin_spikes(ev_array)
		self.assertTrue(is_array_equal_to_file(binned_spikes, "/test_files/input_validate/1_binned_spikes.csv", compare_function=binned_file_comparator))


if __name__ == '__main__':
	unittest.main()