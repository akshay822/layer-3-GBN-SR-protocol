import sys, socket, os, time, pickle, random

'''
Name: Akshay Desai

'''

if(len(sys.argv) == 4):
    inputFile = sys.argv[1]
    portNum = int(sys.argv[2])
    numPackets = int(sys.argv[3])
else:
    print("Too little or too many arguments, please try again")
    sys.exit()

#create internet UDP socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(0)
except:
    print("UDP socket creation failed")

try:
    file = open(inputFile, 'r')
    fileContents = file.readlines()
except:
    print("input file not found in current directory, please try again")
finally:
    file.close()

#send server the protocol
protocol = fileContents[0].rstrip()
s.sendto(protocol.encode(), ("", portNum))
secondLine = fileContents[1].split()

#send server the number of bits to use for sequence numbers
seqNumBits = int(secondLine[0])
s.sendto(str(seqNumBits).encode(), ("", portNum))

#send server the window size, used in SR only, GBN server window is always 1
windowSize = int(secondLine[1])
s.sendto(str(windowSize).encode(), ("", portNum))

print("Bits for sequence number: "+str(seqNumBits))
print("Window Size: "+str(windowSize))
timeout = int(fileContents[2])
segmentSize = int(fileContents[3])
print("Timeout: "+str(timeout)+" microseconds")
print("Segment size is "+str(segmentSize)+" bytes")

#base integer to mark where the start of the window is at any time
base = 0
#sequence numbers start at 1 for this simulation
seqNum = 0
#reference to which packet number we're on
pktNum = 0
window=[]

print("Starting Progam Timer")
programtimer = time.time()

timer = time.time()
lostACK = False

def sendWindow(window):
    #create packet data as a random string (data) of size segmentSize
    data = os.urandom(segmentSize)

    for fullPacket in window:
        packet = pickle.loads(fullPacket)

        response = random.random()

        if(response <= .1):
            response = "checksumError"

            packet=[packet[0]]
            packet.append(data)
            packet.append(response)

            s.sendto(pickle.dumps(packet), ("", portNum))
            print("Re-sending packet with sequence number: "+str(packet[0]))

        elif(response > .9):
            response = "lostPacket"

            packet=[packet[0]]
            packet.append(data)
            packet.append(response)

            s.sendto(pickle.dumps(packet), ("", portNum))
            print("Re-sending packet with sequence number: "+str(packet[0]))

        else:
            response = "correct"

            packet=[packet[0]]
            packet.append(data)
            packet.append(response)

            s.sendto(pickle.dumps(packet), ("", portNum))
            print("Re-sending packet with sequence number: "+str(packet[0]))

def randomResponse():
    response = random.random()
    if(response <= .1):
        response = "checksumError"
        return response
    elif(response >= .9):
        response = "lostPacket"
        return response
    else:
        response = "correct"
        return response

def sendUNACKED(window):
    for fullPacket in window:
        packet = pickle.loads(fullPacket)
        # print(packet[0])
        # print(packet[1])

        if(int(packet[1]) == 0):
            packet[4] = randomResponse()
            newPacket = pickle.dumps(packet)
            s.sendto(newPacket, ("", portNum))
            print("Re-sending packet with sequence number: "+str(packet[0]))



def checkTimer(timenow, timebefore):
    #convert microsends from file to seconds
    if(timenow - timebefore > timeout/1000000):
        return True
    else:
        return False

if(protocol == "GBN"):
    print("Initializing GBN")
    if(windowSize > ((2**seqNumBits)-1)):
        print("GBN will not work. GBN max sender window size is 2^seqNumBits - 1. Please update input file.")
        sys.exit()

    print("Starting timer")
    #check if we're done sending data or the window size is full
    while not ((pktNum >= numPackets) and window):

        if(checkTimer(time.time(), timer)):
            print("Timer expired, resending window!")
            sendWindow(window)
            #resetting timer
            timer = time.time()

        #make sure we're not sending packets outside of our window
        if(len(window) < (windowSize+1)):

            response = random.random()

            #create packet data as a random string (data) of size segmentSize
            data = os.urandom(segmentSize)

            seqNum += 1
            if(seqNum > 2**seqNumBits):
                seqNum = 1

            packet=[seqNum]
            packet.append(data)

            if(response < .1):
                response = "checksumError"

                packet.append(response)

                s.sendto(pickle.dumps(packet), ("", portNum))
                print("Sent packet with sequence number: "+str(seqNum))

                window.append(pickle.dumps(packet))

                continue

            elif(response > .9):
                response = "lostPacket"

                packet.append(response)

                s.sendto(pickle.dumps(packet), ("", portNum))
                print("Sent packet with sequence number: "+str(seqNum))

                window.append(pickle.dumps(packet))

                continue

            else:
                response = "correct"

                packet.append(response)

                s.sendto(pickle.dumps(packet), ("", portNum))
                print("Sent packet with sequence number: "+str(seqNum))

                window.append(pickle.dumps(packet))

                continue

        try:
            ACK = s.recv(65536)

            receivedACK = []
            receivedACK = pickle.loads(ACK)
            recvACK = receivedACK[0]
            response = receivedACK[-1]

            wasACKLost = receivedACK[-2]

            if(wasACKLost == "no"):
                if(response == "correct"):
                    print("Received ACK for: "+str(receivedACK[0]))

                    while(int(receivedACK[1]) > (base) and window):
                        print("sliding window")
                        #resetting timer
                        timer = time.time()

                        #slide window by deleting first entry in window and incrementing base by 1
                        del window[0]
                        #packet number sent increases by 1
                        pktNum += 1
                        base += 1
                        print("Received ACK for packet "+str(pktNum)+" out of all the "+str(numPackets)+" packets.")

                elif(response == "dupACK"):
                    packet = pickle.loads(window[0])
                    print("Duplicate ACK received: "+str(packet[0])+", discarding ACK")

                else:
                    print("timeout ended")
            else:
                print("Lost ACK for: "+str(receivedACK[0]))

        except Exception:
            continue

    finishTime = time.time() - programtimer
    print(str(numPackets)+" packets have been ACKed.")
    print("Done sending packets, goodbye! Time taken: "+str(finishTime))
    sys.exit()

elif(protocol == "SR"):
    print("SR")
    if(windowSize > (2**(seqNumBits-1))):
        print("SR will not work. SR max sender window size is 2^(seqNumBits - 1). Please update input file.")
        sys.exit()

    print("Starting timer")
    #check if we're done sending data or the window size is full
    while not ((pktNum > numPackets) and window):

        if(checkTimer(time.time(), timer)):
            print("Timer expired, resending UNACK'd packets!")
            sendUNACKED(window)
            #resetting timer
            timer = time.time()

            if(len(window) != 0):
                packet = pickle.loads(window[0])
                if(packet[1] == 1):
                    del window[0]



        #make sure we're not sending packets outside of our window
        if(len(window) < windowSize):

            response = random.random()

            #create packet data as a random string (data) of size segmentSize
            data = os.urandom(segmentSize)

            seqNum += 1
            if(seqNum > 2**seqNumBits):
                seqNum = 1


            packet=[seqNum]
            packet.append(0)
            packet.append(data)
            packet.append(False)

            if(response <= .1):
                response = "checksumError"

                packet.append(response)

                s.sendto(pickle.dumps(packet), ("", portNum))
                print("Sent packet with sequence number: "+str(seqNum))

                window.append(pickle.dumps(packet))

                continue

            elif(response > .9):
                response = "lostPacket"

                packet.append(response)

                s.sendto(pickle.dumps(packet), ("", portNum))
                print("Sent packet with sequence number: "+str(seqNum))

                window.append(pickle.dumps(packet))

                continue

            else:
                response = "correct"

                packet.append(response)

                s.sendto(pickle.dumps(packet), ("", portNum))
                print("Sent packet with sequence number: "+str(seqNum))

                window.append(pickle.dumps(packet))

                continue


        try:
            ACK = s.recv(65536)

            receivedACK = []
            receivedACK = pickle.loads(ACK)
            recvACK = receivedACK[0]
            response = receivedACK[-1]

            wasACKLost = receivedACK[-2]

            if((receivedACK[0] - 1) == 0):
                newReceivedACK = 2**(seqNumBits)
            else:
                newReceivedACK = receivedACK[0] - 1


            if(wasACKLost == "no"):
                pktNum += 1
                if(response == "correct"):
                    print("ACK received: "+str(receivedACK[0])+" for packet "+str(newReceivedACK))


                    #set packets in window for received ACKS to be ACK'd
                    counter = 0
                    for fullPacket in window:
                        counter += 1
                        packet = pickle.loads(fullPacket)
                        if(packet[0] == newReceivedACK):
                            packet[1] = 1
                            newPacket = pickle.dumps(packet)
                            window[counter-1] = newPacket
                            #print(pickle.loads(newPacket))
                            break


                    packet = pickle.loads(window[0])
                    if(packet[0] == newReceivedACK):
                        #slide window by 1:
                        print("sliding window")
                        #resetting timer
                        timer = time.time()

                        #slide window by deleting first entry in window and incrementing base by 1
                        del window[0]
                        #packet number sent increases by 1
                        base += 1
                        #print("Received ACK for packet "+str(pktNum)+" out of all the "+str(numPackets)+" packets.")

                    if(pktNum == numPackets):
                        break

                elif(response == "selectiveACK"):

                    print("ACK received: "+str(receivedACK[0])+" for packet "+str(newReceivedACK)+", was previously unACKed.")

                    #set packets in window for received ACKS to be ACK'd
                    counter = 0
                    for fullPacket in window:
                        counter += 1
                        packet = pickle.loads(fullPacket)
                        if(packet[0] == newReceivedACK):
                            packet[1] = 1
                            newPacket = pickle.dumps(packet)
                            window[counter-1] = newPacket
                            #print(pickle.loads(newPacket))
                            break

                    #delete those packets after the first packet in window(if it is the one ACK'd) which have also been ACK'd
                    #otherwise it will skip over them
                    packet = pickle.loads(window[0])
                    if(packet[0] == newReceivedACK):
                        print("sliding window")
                        del window[0]
                        numDelete = 0


                        for fullPacket in window:
                            packet = pickle.loads(fullPacket)
                            if(packet[1] == 1):
                                numDelete += 1
                            else:
                                break

                        while(numDelete > 0):
                            print("sliding window")
                            del window[0]
                            numDelete -= 1


                else:
                    print("timeout ended")
            else:
                print("Lost ACK: "+str(receivedACK[0])+" for packet "+str(newReceivedACK))

                counter = 0
                for fullPacket in window:
                    counter += 1
                    packet = pickle.loads(fullPacket)
                    if(packet[0] == newReceivedACK):
                        packet[3] = True

                    newPacket = pickle.dumps(packet)
                    window[counter-1] = newPacket


        except Exception:
            continue

    finishTime = time.time() - programtimer
    print(str(numPackets)+" total packets have been ACKed.")
    print("Done sending packets, goodbye! Time taken: "+str(finishTime))
    sys.exit()
else:
    print("cant read first line of input file")


s.close()
