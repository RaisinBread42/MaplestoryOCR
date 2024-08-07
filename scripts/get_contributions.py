import numpy
print(numpy.__version__)

import numpy.core._multiarray_umath
abi_version = hex(id(numpy.core._multiarray_umath))
print(abi_version)

import os
import statistics
from datetime import date
from matplotlib import pyplot as plt
import pandas as pd
from PIL import Image
from paddleocr import PaddleOCR
import logging

class FileProcessor:
    def __init__(self, input_folder):
        self.input_folder = input_folder
    
    def list_files(self):
        return [os.path.join(self.input_folder, filename) for filename in os.listdir(self.input_folder)]

    @staticmethod
    def clear_temp_folder():
        temp_folder = "./data/temp"
        if os.path.exists(temp_folder):
            files = os.listdir(temp_folder)
            for file in files:
                file_path = os.path.join(temp_folder, file)
                try:
                    os.remove(file_path)
                except OSError as e:
                    logging.error(f"Error removing file: {file_path}. {e}")

class ImageProcessor:
    def __init__(self, threshold=100):
        self.threshold = threshold
    
    def preprocess(self, image_file):
        image = Image.open(image_file).convert("L")
        image = image.point(lambda p: 0 if p > self.threshold else 255)
        return image
        
    @staticmethod
    def chop(image):
        width, height = image.size
        pixel_values_along_x = [image.getpixel((x, y)) for y in range(height) for x in range(width)]
        standard_dev_y = [statistics.stdev(pixel_values_along_x[y * width: (y + 1) * width]) for y in range(height)]
        low_standard_dev_y = [y for y, stddev in enumerate(standard_dev_y) if stddev < 5]

        y_bounds = [(low_standard_dev_y[i], low_standard_dev_y[i + 1]) for i in range(len(low_standard_dev_y) - 1) if low_standard_dev_y[i + 1] - low_standard_dev_y[i] > 1]

        image_segments = [image.crop((0, y_start - 5, image.width, y_end + 5)) for y_start, y_end in y_bounds]
        return standard_dev_y, image_segments

class OCRProcessor:
    def __init__(self):
        self.ocr_model = None  # Initialize the OCR model as None
    
    def get_ocr_model(self):
        if self.ocr_model is None:
            self.ocr_model = PaddleOCR(lang='en', use_angle_cls=False, show_log=False)
        return self.ocr_model

    def read(self, file_path):
        ocr_model = self.get_ocr_model()  # Lazy initialization of the OCR model
        result = ocr_model.ocr(file_path)
        return [line[1][0] for res in result for line in res]

class DataProcessor:
    @staticmethod
    def process_results(results: list):
        final_results = []
        for result in results:
            scores = result[-3:] # third index from end -> to last index, first index = 1
            person = result[:-3] # beginning to 3 index from end, exlcudes all scores
            name_job_level_title_string = ' '.join(person).replace('.', ' ')#.replace(')', ' ')
            name_job_level_title_list = name_job_level_title_string.split()

            name = name_job_level_title_list[0]

            if len(name_job_level_title_list) < 4: # didn't parse out list properly
                level = 0
                culvert = 0
                flag = 0
                job = "Unknown"
            else:
                level = name_job_level_title_list[-2][-3:]
                culvert = scores[-2]
                flag = scores[-1]

                job = name_job_level_title_string
                job = job.replace(name,'').replace(level,'').split()
                job.pop() # remove last string (rank)
                job = ' '.join(job) if len(job) >= 1 else 'Unknown'


            final_results.append([name, job, level, culvert, flag])

        df = pd.DataFrame(final_results, columns=['IGN', 'CLASS', 'LVL', 'CULVERT', 'FLAG'])
        output_file = f"./data/output/{date.today()}_raw.csv"
        df.to_csv(output_file, index=False)
        print(f"Raw data saved to {output_file}")

class DataExtractor:
    def __init__(self, input_folder, threshold=100):
        self.file_processor = FileProcessor(input_folder)
        self.image_processor = ImageProcessor(threshold)
        self.ocr_processor = OCRProcessor()

    def plot_std_dev_along_y(self, standard_dev_y):
        height = len(standard_dev_y)
        i = range(height)
        plt.plot(i, standard_dev_y)
        plt.xlabel('Y-Coordinate')
        plt.ylabel('Std. Dev')
        plt.title('Std. Dev along Y-axis')
        plt.show()

    def read_segments(self):
        results = []
        for i, file in enumerate(self.file_processor.list_files()):
            try:
                preprocessed_image = self.image_processor.preprocess(file)
            except IOError as e:
                logging.error(f"Error processing file: {file}. {e}")
                continue

            std_dev_y, image_segments = self.image_processor.chop(preprocessed_image)
            for j, segment in enumerate(image_segments):
                try:
                    segment.save(f"./data/temp/{i}_{j}.jpg")
                except IOError as e:
                    logging.error(f"Error saving segment: {i}_{j}.jpg. {e}")
                    continue

                results.append(self.ocr_processor.read(f"./data/temp/{i}_{j}.jpg"))
            # self.plot_std_dev_along_y(std_dev_y)
            # algo to interpret plots(?)
        return results

    def run_extraction(self):
        self.file_processor.clear_temp_folder()
        results = self.read_segments()
        DataProcessor.process_results(results)

if __name__ == '__main__':
    log_file_path = 'logs.txt'
    logging.basicConfig(filename=log_file_path, level=logging.ERROR, format='%(asctime)s [%(levelname)s] %(message)s')

    input_folder = "./data/input"
    threshold = 100
    extractor = DataExtractor(input_folder, threshold)
    extractor.run_extraction()
