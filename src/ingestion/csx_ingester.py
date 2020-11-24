import time
from multiprocessing import Pool
import concurrent.futures as cf

from pathlib import Path
import pika, os, time

from ingestion.csx_clusterer import KeyMatcherClusterer
from ingestion.csx_extractor import CSXExtractorImpl
from ingestion.interfaces import CSXIngester
from models.elastic_models import Cluster, KeyMap
from services.elastic_service import ElasticService

def ingest_paper_parallel_func(filepath):
    papers = CSXExtractorImpl().extract_textual_data(filepath)
    KeyMatcherClusterer().cluster_papers(papers)

class CSXIngesterImpl(CSXIngester):
    def __init__(self):
        self.extractor = CSXExtractorImpl()
        self.clusterer = KeyMatcherClusterer()
        self.elastic_service = ElasticService()
        # url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/%2f')
        # params = pika.URLParameters(url)
        # self.connection = pika.BlockingConnection(params)
        # self.channel = self.connection.Channel()
        # self.channel.queue_declare(queue='extractor')

    def ingest_batch_parallel(self, teiDirectoryPath):
        start_time = time.time()
        pool = Pool()
        pool.map(ingest_paper_parallel_func, iter(Path(teiDirectoryPath).rglob("*.[tT][eE][iI]")))
        pool.close()
        pool.join()
        print("--- %s seconds ---" % (time.time() - start_time))

    def ingest_batch_parallel_files(self, fileList):
        # Cluster.init(using=CSXIngesterImpl().elastic_service.get_connection())
        # KeyMap.init(using=CSXIngesterImpl().elastic_service.get_connection())
        start_time = time.time()
        # pool = Pool()
        # for each_file in fileList:
        #     ingest_paper_parallel_func(each_file)
        # # pool.apply_async(ingest_paper_parallel_func, fileList)
        # pool.close()
        # pool.join()
        with cf.ThreadPoolExecutor(max_workers=1000) as executor:
            for filenow in fileList:
                executor.submit(ingest_paper_parallel_func, filenow)
            # pool.apply_async(ingest_paper_parallel_func, fileList)
            # pool.close()
            # pool.join()
        print("--- %s seconds ---" % (time.time() - start_time))


    def ingest_paper(self, filePath):
        # Cluster.init(using=CSXIngesterImpl().elastic_service.get_connection())
        # KeyMap.init(using=CSXIngesterImpl().elastic_service.get_connection())
        print("ingesting-->", filePath)
        papers = CSXExtractorImpl().extract_textual_data(filePath)
        # baseResultsPath = config.get('ExtractionConfigurations', 'baseResultsPath')
        KeyMatcherClusterer().cluster_papers(papers)

    def ingest_batch(self, dirpath):
        count = 0
        start_time = time.time()
        self.extractor.batch_extract_textual_data(dirpath)
        all_files = list(Path(dirpath).rglob("*.[tT][eE][iI]"))
        for filepath in all_files:
            count = count + 1
            if count % 20 == 0:
                print(count)
                print("--- %s seconds ---" % (time.time() - start_time))
            papers = self.extractor.extract_textual_data(filepath=str(filepath))
            self.clusterer.cluster_papers(papers)
        print("--- %s seconds ---" % (time.time() - start_time))


    def docs_generator(self, dirPath=None):
        count = 0
        all_files = list(Path(dirPath).rglob("*.[tT][eE][iI]"))
        for filepath in all_files:
            count = count + 1
            if count % 20 == 0:
                print(count)
            paper, citations = self.extractor.extract_textual_data(str(filepath))
            yield paper.to_dict(True)
            for citation in citations:
                yield citation.to_dict(True)

    def pdf_process_function(msg):
        print(" PDF processing")
        print(" [x] Received " + str(msg))

        time.sleep(5)  # delays for 5 seconds
        print(" PDF processing finished");
        return

    def pull_from_queue(self):
        pass

if __name__ == "__main__":
    csx_ingester = CSXIngesterImpl()
    Cluster.init(using=csx_ingester.elastic_service.get_connection())
    KeyMap.init(using=csx_ingester.elastic_service.get_connection())
    # KeyMap.init(using=csx_ingester.elastic_service.get_connection())
    # csx_ingester.ingest_batch_parallel("/data/sfk5555/ACL_results/2020072500")