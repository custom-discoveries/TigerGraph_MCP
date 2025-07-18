#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
# mcp_logger.py: Sets up the log handler and sets Logging Level to ERROR
#******************************************************************************

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

def setErrorHandler():
 
    # Create and configure a handler
    handler = logging.StreamHandler()
    handler.setLevel(logger.level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)    