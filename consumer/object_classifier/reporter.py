class ClassificationReporter:

    def __init__(
            self,
            event_time,
            ingestion_time,
            processed_time,
            actual_label,
            prediction,
            matched
        ):
        self.event_time = event_time
        self.ingestion_time = ingestion_time
        self.processed_time = processed_time
        self.actual_label = actual_label
        self.prediction = prediction
        self.matched = matched
        self.inference_time = self.get_inference_time()
        self.processing_time = self.get_processing_time()
        self.queueing_delay = self.get_queueing_delay()

    def get_inference_time(self):
        return self.processed_time - self.ingestion_time

    def get_processing_time(self):
        return self.processed_time - self.event_time

    def get_queueing_delay(self):
        return self.ingestion_time - self.event_time

    def is_correctly_classified(self):
        return self.matched
