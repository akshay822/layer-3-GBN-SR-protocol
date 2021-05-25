import sys, os, socket, pickle, random, time

'''
Name: Akshay Desai

'''


if(len(sys.argv) == 2):
    portNum = int(sys.argv[1])
else:
    print("Too little or too many arguments")

#create internet UDP socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except:
    print("UDP socket creation failed")

try:
    s.bind(("", portNum))
    print("server running!")
except:
    print("socket binding to port number failed, port number may be busy or illegitimate")

try:
    data, addr = s.recvfrom(65536)
    protocol = data.decode()
    print(protocol)

    data, addr = s.recvfrom(65536)
    seqNumBits = int(data.decode())
    maxSeqNum = (2**seqNumBits)
    print("Bits given for sequence number: "+data.decode())

    data, addr = s.recvfrom(65536)
    windowSize = int(data.decode())
    if(protocol == "SR"):
        print("Window size is: "+str(windowSize))
except:
    print("Could not receive any data.")

window=[]

expectedSeqNum = 1
totalPackets = 0

if(protocol == "GBN"):
    print("Initializing GBN")
    while True:
        data, addr = s.recvfrom(65536)
        receivedPacket = pickle.loads(data)

        #print(receivedPacket[-1])
        response = receivedPacket[-1]

        willACKLose = random.random()

        if(willACKLose <= .05):
            willACKLose = "lostACK"
        else:
            willACKLose = "no"

        if(receivedPacket[0] == expectedSeqNum):
            if(response == "correct"):
                expectedSeqNum += 1
                totalPackets += 1

                if(expectedSeqNum > maxSeqNum):
                    expectedSeqNum = 1

                ackPacket = [expectedSeqNum]
                ackPacket.append(totalPackets)
                ackPacket.append(willACKLose)
                ackPacket.append(response)
                try:
                    print("Received packet: "+str(receivedPacket[0]))
                    s.sendto(pickle.dumps(ackPacket), (addr[0], addr[1]))
                    print("Sending ACK: "+str(expectedSeqNum))
                except Exception:
                    print("didnt send ack to client")

            elif(response == "checksumError"):
                print("checksum error, discarding packet sequence number: "+str(receivedPacket[0]))

            elif(response == "lostPacket"):
                print("Packet "+str(receivedPacket[0])+" was lost on way to server")

            else:
                print("actual udp error occurred")

        else:
            if(response == "correct"):
                print("Received packet: "+str(receivedPacket[0])+", OUT OF ORDER, discarding packet: "+str(receivedPacket[0]))
                print("Resending ACK: "+str(expectedSeqNum))

                ackPacket = [expectedSeqNum]
                ackPacket.append(totalPackets)
                ackPacket.append(willACKLose)
                ackPacket.append("dupACK")

                s.sendto(pickle.dumps(ackPacket), (addr[0], addr[1]))
            elif(response == "checksumError"):
                print("checksum error, discarding packet sequence number: "+str(receivedPacket[0]))
            elif(response == "lostPacket"):
                print("Packet "+str(receivedPacket[0])+" was lost on way to server")
            else:
                print("actual udp error occurred")


elif(protocol == "SR"):
    print("Initializing SR")
    while True:
        data, addr = s.recvfrom(65536)
        receivedPacket = pickle.loads(data)

        #print(receivedPacket[-1])
        response = receivedPacket[-1]

        willACKLose = random.random()

        if(willACKLose <= .05):
            willACKLose = "lostACK"
        else:
            willACKLose = "no"


        ackNumber = int(receivedPacket[0])+1
        if(ackNumber > maxSeqNum):
            ackNumber = 1


        if(len(window) < windowSize):
            if(expectedSeqNum > maxSeqNum):
                expectedSeqNum = 1

            totalPackets += 1
            if(receivedPacket[0] == expectedSeqNum):
                if(response == "correct"):
                    expectedSeqNum += 1
                    if(expectedSeqNum > maxSeqNum):
                        expectedSeqNum = 1

                    ackPacket = [ackNumber]
                    ackPacket.append(totalPackets)
                    ackPacket.append(1)
                    ackPacket.append(willACKLose)
                    ackPacket.append(response)

                    window.append(pickle.dumps(ackPacket))
                    try:
                        print("Received packet: "+str(receivedPacket[0]))
                        s.sendto(pickle.dumps(ackPacket), (addr[0], addr[1]))
                        print("Sending ACK: "+str(expectedSeqNum))
                    except:
                        print("didnt send ack to client")

                    print("sliding window")

                    #slide window by deleting first entry in window
                    del window[0]


                elif(response == "checksumError"):

                    print("checksum error, discarding packet sequence number: "+str(receivedPacket[0]))

                    ackPacket = [ackNumber]
                    ackPacket.append(totalPackets)
                    ackPacket.append(0)
                    ackPacket.append(willACKLose)
                    ackPacket.append("dupACK")

                    window.append(pickle.dumps(ackPacket))
                elif(response == "lostPacket"):

                    print("Packet "+str(receivedPacket[0])+" was lost on way to server")

                    ackPacket = [ackNumber]
                    ackPacket.append(totalPackets)
                    ackPacket.append(0)
                    ackPacket.append(willACKLose)
                    ackPacket.append("dupACK")

                    window.append(pickle.dumps(ackPacket))
                else:
                    print("actual udp error occurred")

            else:

                if(receivedPacket[-2] == True):
                    print("Received DUPLICATE packet: "+str(receivedPacket[0])+" meaning ACK was LOST")
                    print("Re-sending ACK: "+str(ackNumber))

                    ackPacket = [ackNumber]
                    ackPacket.append(totalPackets)
                    ackPacket.append(1)
                    ackPacket.append(willACKLose)
                    ackPacket.append("selectiveACK")

                    s.sendto(pickle.dumps(ackPacket), (addr[0], addr[1]))
                    continue

                else:

                    alreadyInWindow = False
                    for fullPacket in window:
                        packet = pickle.loads(fullPacket)
                        if(packet[0] == ackNumber):
                            alreadyInWindow = True


                    if(response == "correct"):

                        print("Received packet: "+str(receivedPacket[0]))
                        print("Packet received OUT OF ORDER: "+str(receivedPacket[0]))

                        print("Sending ACK: "+str(ackNumber))


                        ackPacket = [ackNumber]
                        ackPacket.append(totalPackets)
                        ackPacket.append(1)
                        ackPacket.append(willACKLose)
                        ackPacket.append("selectiveACK")


                        if(alreadyInWindow == False):
                            window.append(pickle.dumps(ackPacket))



                        s.sendto(pickle.dumps(ackPacket), (addr[0], addr[1]))
                    elif(response == "checksumError"):

                        print("checksum error, discarding packet sequence number: "+str(receivedPacket[0]))

                        ackPacket = [ackNumber]
                        ackPacket.append(totalPackets)
                        ackPacket.append(0)
                        ackPacket.append(willACKLose)
                        ackPacket.append("dupACK")

                        if(alreadyInWindow == False):
                            window.append(pickle.dumps(ackPacket))
                    elif(response == "lostPacket"):

                        print("Packet "+str(receivedPacket[0])+" was lost on way to server")

                        ackPacket = [ackNumber]
                        ackPacket.append(totalPackets)
                        ackPacket.append(0)
                        ackPacket.append(willACKLose)
                        ackPacket.append("dupACK")

                        if(alreadyInWindow == False):
                            window.append(pickle.dumps(ackPacket))
                    else:
                        print("actual udp error occurred")

        else:
            #buffer is full, waiting on NACK'd packets in buffer
            print("buffer is full, waiting on NACK'd packets in buffer")

            if(response == "correct"):
                numDelete = 0
                for fullPacket in window:
                    packet = pickle.loads(fullPacket)

                    if(packet[0] == ackNumber):

                        ackPacket = [ackNumber]
                        ackPacket.append(totalPackets)
                        ackPacket.append(1)
                        ackPacket.append(willACKLose)
                        ackPacket.append("selectiveACK")

                        print("Received packet: "+str(receivedPacket[0]))
                        print("Sending ACK: "+str(ackNumber))
                        s.sendto(pickle.dumps(ackPacket), (addr[0], addr[1]))

                    if((packet[0] == ackNumber) or (packet[2] == 1)):
                        print("sliding window")
                        numDelete += 1

                while(numDelete > 0):
                    del window[0]
                    expectedSeqNum += 1
                    if(expectedSeqNum > maxSeqNum):
                        expectedSeqNum = 1
                    numDelete -= 1

            elif(response == "checksumError"):
                print("checksum error, discarding packet sequence number: "+str(receivedPacket[0]))

            elif(response == "lostPacket"):
                print("Packet "+str(receivedPacket[0])+" was lost on way to server")

            else:
                print("actual udp error occurred")


else:
    print("Cannot read the type of protocol. Please try again.")
    sys.exit()
