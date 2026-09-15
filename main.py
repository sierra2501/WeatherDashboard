from package import logging_config
logging_config.setup_logging()

import logging
logger = logging.getLogger(__name__)

import jma_xml
import yohou
import gaikyo

def main():
    logger.info('////////// START //////////')
    jma_xml.main()
    yohou.main()
    gaikyo.main()

if __name__ == "__main__":
    main()