"""
This file implements the analysis pipeline used to produce suggested
highlight segments of a podcast episode.
"""
import json


class Highlighter():

    def __init__(self):
        self.results = {}
        self.max_id = -1

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
