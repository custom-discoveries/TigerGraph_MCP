#******************************************************************************
# Copyright (c) 2025, Custom Discoveries LLC. (www.customdiscoveries.com)
# All rights reserved.
#
# system_Services.py: This modelue defines the SystemUtilities class for
# accessing TigerGraph administration services to the graph database
#******************************************************************************
import sys

from typing import List
from mcp_server.tigerGraph.services import TigerGraph_Session
from mcp_server.mcp_logger import setErrorHandler, logger

class SystemUtilities:

    def __init__(self,session:TigerGraph_Session):
        self.session = session
        setErrorHandler()
        self.version = self.extractVersionNumber()

    def extractVersionNumber(self) -> float:
        try:
            results = self.session.getConnection().getVersion()
            if (len(results) > 0):
                versionString = results[0]['version']
                versionNumber = (versionString.split("_"))[1]
                version = versionNumber.split(".")
                versionNumber = f"{version[0]}.{version[1]}"
                if versionNumber !="":
                    return float(versionNumber)
                else:
                    return (0.0)

        except ValueError as error:
            logger.error(f"Error in extractVersionNumber() {error} -> {version}")
        except Exception as err:
             logger.error(f"Error on Get Version Call.. {err}")
             logger.error("Please create a Secret/Token to view database Version...")
             raise Exception(err)


    def displayComponentVersion(self) -> List[str]:
        status:List[str]=[]
        try:
            results = self.session.getConnection().getVersion()
            status.append("\n")
            for cmp in results:
                status.append(f"%-21s %25s" % (cmp.get('name'),cmp.get('version')) )

        except Exception as err:
             logger.error(f"Error on Get Version Call.. {err}")
             logger.error("Please create a Secret/Token to view database Version...")

        return status

    def displayServicesStatus(self) -> List[str]:
        """
        This function is designed to work with TigerGraph V4.2 or greater.
        """
        status:List[str]=[]
        try:
            if (self.version >= 4.2):
                _serviceDescriptor = {"ServiceDescriptors": [ {"ServiceName":"ADMIN"},
                                                            {"ServiceName":"CTRL"},
                                                            {"ServiceName":"DICT"},
                                                            {"ServiceName":"ETCD"},
                                                            {"ServiceName":"EXE"},
                                                            {"ServiceName":"GPE"},
                                                            {"ServiceName":"GSE"},
                                                            {"ServiceName":"GSQL"},
                                                            {"ServiceName":"GUI"},
                                                            {"ServiceName":"IFM"},                                                          
                                                            {"ServiceName":"KAFKA"},
                                                            {"ServiceName":"KAFKACONN"},
                                                            {"ServiceName":"KAFKASTRM-LL"},
                                                            {"ServiceName":"NGINX"},
                                                            {"ServiceName":"RESTPP"},
                                                            {"ServiceName":"ZK"}
                                                            ]}

                results = self.session.getConnection().getServiceStatus(_serviceDescriptor)

                for se in results["ServiceStatusEvents"]:
                    sd = se["ServiceDescriptor"]
                    serviceName = sd["ServiceName"]
                    serviceStatus = se["ServiceStatus"]
                    processState = se["ProcessState"]
                    f"%-8s %7s %7s" % (serviceName, serviceStatus, processState)
                    status.append(f"%-8s %7s %7s" % (serviceName, serviceStatus, processState))
            else:
                status.append(f"displayServicesStatus does NOT support TigerGraph Versions {self.version}")
        except Exception as error:
            logger.error(f"displayServicesStatus() Error: {error}", file=sys.stderr)

        return status

    def displayAllJobs(self) -> List:
        status:List[str]=[False]
        try:
            conn = self.session.getConnection()
            results = conn.gsql(f"USE GRAPH {conn.graphname} SHOW LOADING STATUS ALL")
            inter = (results.split('\n'))
            status[0]= f"Aborted = {(results.find("aborted") >=0)}"
            status.append(inter[2])
            return status
        except Exception as error:
            logger.error(f"ERROR in Aborting Jobs: {error}")

    def abortAllJobs(self) -> bool:

        try:
            conn = self.session.getConnection()
            results = conn.gsql("USE GRAPH "+conn.graphname+" ABORT LOADING JOB ALL")
            print(results)
            if results.find("aborted") >=0:
                return True
            else:
                return False
        except Exception as error:
            logger.error(f"ERROR in Aborting Jobs: {error}")


    def checkGraphExists(self) -> bool:

      try:
            self.session.getConnection()
            return self.session.getConnection().check_exist_graphs(self.session.getConnection().graphname)
      except Exception as e:
        logger.error("Error Checking Graph Status: ", e)

        return False

    #
    # Display all the components version numbers
    # Note: you need a valid Secret / Token to call the getVersion() function
    #

    def displayCPUMemoryStatus(self) -> List[str]:
        status:List[str]=[]
        try:
            results = self.session.getConnection().getSystemMetrics(latest=1,what='cpu-memory') 

            status.append("\nCPU & Memory Utilitzation Report\n")

            status.append(f"{'Service':17s} {'CPU Usage':12s} {'Memory Usage':11s}")
            status.append("-" * 43)
            for aMetric in results.get('CPUMemoryMetrics'):
                service = aMetric.get('ServiceDescriptor').get('ServiceName')
                cpu = aMetric.get('CPU').get('CPUUsage')
                memory = aMetric.get('Memory').get('MemoryUsageMB')
                cpu = 0 if cpu == None else cpu
                
                status.append(f"{service:15s} {cpu:11,.5f} {memory:12,.0f} MB")

        except Exception as error:
             logger.error(f"Error on Display Cpu/Memory Status: {error}")

        return status
    
    def displayDiskStatus(self):
        status:List[str]=[]
        try:
            results = self.session.getConnection().getSystemMetrics(latest=1,what='diskspace') 

            totalDiskSpace = 0
            diskSpaceUsed = 0
            diskSpaceFree = 0
            status.append("\nDisk Space Utilitzation Report\n")

            for aMetric in results.get('DiskMetrics'):
                disk = aMetric.get('Disk')
                status.append(f"Path Name: {disk.get('PathName')}")
                status.append(f"Path: {disk.get('Path')}")
                status.append(f"Size: {disk.get('SizeMB'):,.2f} MB\n")
                diskSpaceUsed += disk.get('SizeMB')
                diskSpaceFree = disk.get("FreeSizeMB")

            totalDiskSpace = diskSpaceUsed + diskSpaceFree
            status.append(f"Disk Space Used: {diskSpaceUsed/1000:,.2f} GB")
            status.append(f"Disk Space Free: {diskSpaceFree/1000:,.2f} GB")
            status.append(f"Total Disk Space Allocated: {totalDiskSpace/1000:,.2f} GB")


        except Exception as error:
             logger.error(f"Error on Display Disk Status for iCloud Version {error}")

        return status
    
    def displayDetailedServicesStatus(self):
        status:List[str]=[]
        try:
            results = self.displayServicesStatus()
            status.extend(results)

            conn = self.session.getConnection()

            status.append("\nDisplaying Detailed Server status:")
            results = conn.gsql("USE GRAPH "+conn.graphname+" ls")
            interm = results.split("\n")
            status.extend(interm)

        except Exception as error:
            logger.error("displayDetailedServicesStatus() Error:",error)

        return status
    
 