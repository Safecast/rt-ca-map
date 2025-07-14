'''bootstrap.py - Bootstrap the application database from a list of device URNs.
'''

import asyncio
import fetcher

asyncio.run(fetcher.bootstrap_database())

