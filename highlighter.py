"""
This file implements the analysis pipeline used to produce suggested
highlight segments of a podcast episode.
"""
import json
import math
from operator import itemgetter

import spacy
import pytextrank
from nltk.tokenize import TweetTokenizer


class Highlighter():

    """
    Store highlights id/result and load spaCy pipeline for English
    """
    def __init__(self):
        self.results = {}
        self.max_id = 0
        self.nlp = spacy.load("en_core_web_lg")
        self.nlp.add_pipe("textrank", last=True)

    """
    Extractive summarization implementation using PyTextRank
    Reference: https://derwen.ai/docs/ptr/
    """
    def segment_rank(self, text):
        parsed = self.nlp(text)
        seg_bounds = [ [s.start, s.end, set()] for s in parsed.sents ]
        unit_vector = []
        phrase_id = 0
        phrase_limit = len(parsed._.phrases)//10

        # Create segment vectors
        for phrase in parsed._.phrases:
            unit_vector.append(phrase.rank)
            
            for chunk in phrase.chunks:
                # Add phrase to segment vector if phrase falls within segment
                for seg_start, seg_end, seg_vector in seg_bounds:
                    if chunk.start >= seg_start and chunk.end <= seg_end:
                        seg_vector.add(phrase_id)      
                        break
            phrase_id += 1

            # Consider only top 10% of ranked phrases
            if phrase_id == phrase_limit:
                break
        
        # Compute Euclidean distance between unit vector and segment vectors
        sum_ranks = sum(unit_vector)
        unit_vector = [ rank/sum_ranks for rank in unit_vector ]
        seg_rank = {}
        seg_id = 0

        for seg_start, seg_end, seg_vector in seg_bounds:
            sum_sq = 0.0

            for phrase_id in range(len(unit_vector)):
                if phrase_id not in seg_vector:
                    sum_sq += unit_vector[phrase_id]**2.0

            seg_rank[seg_id] = math.sqrt(sum_sq)
            seg_id += 1

        # Compile all segments
        seg_text = {}
        seg_id = 0

        for seg in parsed.sents:
            seg_text[seg_id] = seg.text
            seg_id += 1

        # Order segments by lowest distance
        results = []

        for seg_id, _ in sorted(seg_rank.items(), key=itemgetter(1)):
            results.append(seg_text[seg_id])

        return results

    """
    Retrieve start and end time of segment specified by start and end index.
    """
    def find_bounds(self, word_times, start_index, end_index):
        found_start = False
        found_end = False
        start_time = 0.0
        end_time = 0.0

        # Find first token with associated pronunciation time
        while not found_start:
            if word_times[start_index]["type"] == "pronunciation":
                start_time = word_times[start_index]["start_time"]
                found_start = True
            start_index += 1

        # Find last token with associated pronunciation time
        while not found_end:
            if word_times[end_index]["type"] == "pronunciation":
                end_time = word_times[end_index]["end_time"]
                found_end = True
            end_index -= 1

        return (start_time, end_time)

    """
    Compute times of popular segments and select popular segments to fulfill
    the given highlights reel time duration.
    """
    def get_times(self, segments, word_times, text, time):
        duration = 0.0
        clips = []

        for segment in segments:
            # Use Tweet tokenizer because other spaCy/NLTK tokenizers make
            # errors by incorrectly splitting tokens (e.g. She'd -> She, 'd)
            tokenizer = TweetTokenizer()
            tokens = tokenizer.tokenize(segment)
            tokens_len = len(tokens)
            
            # Count number of occurences of token prior to segment start token
            first_token = tokens[0]
            all_tokens = tokenizer.tokenize(text[:text.find(segment)])
            num_occur = all_tokens.count(first_token)    
            expected_pos = num_occur+1
            seen = 0

            for index in range(len(word_times)):
                word_time = word_times[index]

                # Count number of occurences of token that we've already seen
                if word_time["alternatives"][0]["content"] == first_token:
                    seen += 1

                    # Check whether we have reached our segment start token
                    if seen == expected_pos:
                        # Retrieve start and end time of segment
                        start_time, end_time = self.find_bounds(word_times, 
                            index, index+tokens_len-1)
                        
                        clips += [{
                            "start_time": start_time, 
                            "end_time": end_time
                        }]
                        duration += end_time-start_time
                        
                        # Return highlight clips once we fulfill the duration
                        if duration >= time:
                            clips.sort(key=lambda clip: clip["start_time"])

                            return clips, duration

        # Return gathered clips if fulfilling given duration isn't possible
        clips.sort(key=lambda clip: clip["start_time"])

        return clips, duration

    """
    Create and store suggested highlights for transcripts in given file.
    The duration of highlight clip should be roughly equal to the given time.
    Expected structure of input JSON file:
        {
            transcriber,
            created,
            results: {
                transcripts: [
                    {
                        transcript,
                        confidence
                    },
                    ...
                ],
                items: [
                    {
                        start_time,
                        end_time,
                        alternatives: [
                            {
                                content,
                                confidence
                            },
                            ...
                        ],
                        type,
                        metadata: {
                            human_segment_id
                        }
                    },
                    ...
                ]
            }
                
        }
    """
    def analyze(self, time, file):
        self.max_id += 1
        self.results[self.max_id] = []

        # Load full-text transcripts and associated word pronunciation times
        json_data = json.load(file.file)
        transcripts = json_data["results"]["transcripts"]
        word_times = json_data["results"]["items"]
        transcript_id = 0

        for transcript in transcripts:
            transcript_id += 1
            transcript = transcript["transcript"]

            # Rank segments by importance in summarizing the text
            segments_ranked = self.segment_rank(transcript)
            # Select most popular segments that fulfill given highlights time
            highlights, duration = self.get_times(segments_ranked, word_times, 
                                                    transcript, time)
            
            # Compile information for single transcript in given file
            transcript_highlights = {
                "transcript_id": transcript_id,
                "duration": duration,
                "highlights": highlights
            }
            self.results[self.max_id].append(transcript_highlights)
            
        return self.max_id

    """
    Retrieve highlights suggested for transcripts from file with given id.
    Expected structure of output JSON file:
        {
            file_id,
            results: [
                {
                    transcript_id,
                    duration,
                    highlights: [
                        {
                            start_time,
                            end_time
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    def highlights(self, id):
        return self.results[id]
