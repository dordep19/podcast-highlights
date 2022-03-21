"""
This file implements the analysis pipeline used to produce suggested
highlight segments of a podcast episode.
"""
import json
import math
from operator import itemgetter

import spacy
import pytextrank


class Highlighter():

    """
    Store highlights id/result and load Spacy pipeline for English
    """
    def __init__(self):
        self.results = {}
        self.max_id = -1
        self.nlp = spacy.load("en_core_web_lg")
        self.nlp.add_pipe("textrank", last=True)

    """
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
    def analyze(self, file):
        json_data = json.load(file.file)
        entries = json_data["results"]["transcripts"]
        transcript_id = -1

        for entry in entries:
            transcript_id += 1
            transcript = entry["transcript"]
            sents_ranked = self.sentence_rank(transcript)
            
    """
    Extractive summarization implementation using PyTextRank
    Reference: https://derwen.ai/docs/ptr/
    """
    def sentence_rank(self, text):
        parsed = self.nlp(text)
        sent_bounds = [ [s.start, s.end, set()] for s in parsed.sents ]
        unit_vector = []
        phrase_id = 0
        phrase_limit = len(parsed._.phrases)//10
        
        # Populate phrase vectors of sentences
        for phrase in parsed._.phrases:
            unit_vector.append(phrase.rank)
            
            for chunk in phrase.chunks:
                for sent_start, sent_end, sent_vector in sent_bounds:
                    if chunk.start >= sent_start and chunk.end <= sent_end:
                        sent_vector.add(phrase_id)      
                        break
            phrase_id += 1

            # Use only top 10% of ranked phrases
            if phrase_id == phrase_limit:
                break
        
        # Compute Euclidean distance between unit and sentence phrase vectors
        sum_ranks = sum(unit_vector)
        unit_vector = [ rank/sum_ranks for rank in unit_vector ]
        sent_rank = {}
        sent_id = 0

        for sent_start, sent_end, sent_vector in sent_bounds:
            sum_sq = 0.0

            for phrase_id in range(len(unit_vector)):
                if phrase_id not in sent_vector:
                    sum_sq += unit_vector[phrase_id]**2.0

            sent_rank[sent_id] = math.sqrt(sum_sq)
            sent_id += 1

        # Compile all sentences
        sent_text = {}
        sent_id = 0

        for sent in parsed.sents:
            sent_text[sent_id] = sent.text
            sent_id += 1

        # Order sentences by lowest distance
        results = []

        for sent_id, _ in sorted(sent_rank.items(), key=itemgetter(1)):
            results.append((sent_id, sent_text[sent_id]))

        return results

    """
    Expected structure of output JSON file:
        {
            id,
            highlights: [
                {
                    id,
                    start_time,
                    end_time
                },
                ...
            ]
        }
    """
    def highlights(self, id):
        return self.results[id]
