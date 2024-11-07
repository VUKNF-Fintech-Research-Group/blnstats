import os
import ipaddress

class IPGeolocation:
    # https://www.iwik.org/ipcountry/LT.cidr
    allNetworks = {'IPv4': {}, 'IPv6': {}}

    @staticmethod
    def loadGeoNetworks():
        cidrFolder = "./IPGeo/"
        
        filenames = next(os.walk(cidrFolder), (None, None, []))[2]
        for filename in filenames:
            
            if(filename in [".DS_Store"]):
                continue

            countryCode = filename.split('.')[0]

            addressType = ''
            if(filename.endswith(".cidr")):
                addressType = 'IPv4'
                IPGeolocation.allNetworks['IPv4'][countryCode] = []
            elif(filename.endswith(".ipv6")):
                addressType = 'IPv6'
                IPGeolocation.allNetworks['IPv6'][countryCode] = []

            with open(f"{cidrFolder}/{filename}", "r") as f:
                for line in f.readlines():
                    line = line.strip()
                    if(not line.startswith("#")):
                        if(line != ""):
                            IPGeolocation.allNetworks[addressType][countryCode].append(line)

    @staticmethod
    def getIPCountry(ipAddress):
        addressType = ''
        if('.' in ipAddress):
            addressType = 'IPv4'
        elif(':' in ipAddress):
            addressType = 'IPv6'

        for countryCode in IPGeolocation.allNetworks[addressType]:
            countrySubnets = IPGeolocation.allNetworks[addressType][countryCode]

            for ipSubnet in countrySubnets:
                if(ipaddress.ip_address(ipAddress) in ipaddress.ip_network(ipSubnet, False)):
                    return countryCode

        return ''

# Initialize the IP Geolocation data
IPGeolocation.loadGeoNetworks()

# Example usage:
# print(json.dumps(IPGeolocation.allNetworks, indent=4))