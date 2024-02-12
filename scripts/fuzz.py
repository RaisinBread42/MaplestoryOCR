import os
import pandas as pd
from datetime import date
from thefuzz import fuzz, process
from termcolor import colored

class IGNMatcher:
    def __init__(self, input_file, choices_file, classes_choices_file, min_score_threshold=80):
        self.input_file = input_file
        self.choices_file = choices_file
        self.classes_choices_file =  classes_choices_file
        self.min_score_threshold = min_score_threshold

    def process_raw_igns(self, raw, choices):
        matched_ign, score = process.extractOne(raw, choices, scorer=fuzz.token_sort_ratio)
        if score < self.min_score_threshold:
            print(colored(f"fuzz.py unable to find match for {raw}", 'red'))
            return (f"{raw}[?]", score)
        return (matched_ign, score)

    def process_raw_classes(self, raw, choices):
        matched_class, score = process.extractOne(raw, choices, scorer=fuzz.token_sort_ratio)
        if score < 60: #self.min_score_threshold:
            print(colored(f"fuzz.py unable to find match for {raw}", 'red'))
            return (f"{raw}[?]", score)
        return (matched_class, score)

    def match_igns(self):
        df = pd.read_csv(self.input_file)

        #fuzz igns
        raw_igns = df['IGN'].tolist()
        choices = pd.read_csv(self.choices_file)['IGN'].tolist()
        matched_igns = [self.process_raw_igns(raw_ign, choices)[0] for raw_ign in raw_igns]

        new_ign_df = pd.DataFrame({'IGN': matched_igns})

        #fuzz classes
        raw_classes = df['CLASS'].tolist()
        class_choices = pd.read_csv(self.classes_choices_file)['CLASS'].tolist()
        matched_classes = [self.process_raw_classes(raw_class, class_choices)[0] for raw_class in raw_classes]

        new_class_df = pd.DataFrame({'CLASS': matched_classes})
        
        df_dropped = df.drop('IGN', axis=1).drop('CLASS', axis=1)
        df = pd.concat([new_ign_df, new_class_df, df_dropped], axis=1)

        output_file = f"./data/output/{date.today()}.csv"
        df.to_csv(output_file, index=False)
        print(f"Matched IGN data saved to {output_file}")

def main():
    input_file = f"./data/output/{date.today()}_raw.csv"
    choices_file = "./data/guild_assets/igns.csv"
    classes_choices_file = "./data/guild_assets/classes.csv"
    ign_matcher = IGNMatcher(input_file, choices_file, classes_choices_file)
    ign_matcher.match_igns()

if __name__ == "__main__":
    main()