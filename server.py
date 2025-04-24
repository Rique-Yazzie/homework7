'''
	
	CS460(Spring-2025)	
	Homework-3: Server program for the text-based 
						 chat application. Server is 
                         implemeneted as a Python class.
	Author:
		Nazmul(mh2752@nau.edu)

'''
import socket
from select import select
import sys


# -------------------------------------- Server Class -----------------------------------------------

class ChatServer:


    # -------------------- Class Private Member Variables ----------------------

    # A dictinary for storing chat room names and the list of 
    # 2-tuples of active participants' sockets and user ids:
    __dictionary_chat_room_participants = None # Dictionary format: key="chatroom_name",value=[(participant_1_socket,participant_1_user_id),.....,(participant_n_socket,participant_n_user_id)]

    # A list of all active sockets, including the server:
    __list_all_active_sockets = None


    # A dictionary to maintain the 'current state' 
    # of a connected client in joining the 
    # chat server:
    __dictionary_client_current_state = None # Dictionary format: key = (client_ip,client_port), value = #state_number
                                             #
                                             # All finite client state numbers:
                                             #                           None = client is joining for the first time (new connection request)
                                             #                           0 = initial connection request accepted and welcome message sent
                                             #                           1 = client's user id obtained and sent join choice
                                             #                           2 = client has made a join choice
                                             #                           3 = client has provided chat room name and joined it
    
    # A dictionary to maintain the choices 
    # made by the client at states 
    # 1, 2, and 3
    __dictionary_clients_choices = None #  Dictionary format: key = (client_ip,client_port), value = [user id, join choice, chat room name]



    # TCP port number for the server to listen 
    # for incoming client requests:
    __server_port_number = None

    # IP address of the server:
    __server_ip_address = None

    # Handle for server socket:
    __server_socket = None

    # Flag to control the server's 
    # running status:
    __server_keep_running = None

    # Maximum number of clients to 
    # be allowed to wait in the 
    # buffer by the server socket:
    __MAX_CLIENTS = None

    # Maximum length of the buffer 
    # for receiving messages 
    # from client:
    __MAX_BUFFER_LENGTH = None 



    # ------------------------------------ Class Initializer/Constructor ----------------------------
    def __init__(self):
        
        # Print dialog:
        print("Initializing chat server...")

        # Initialize class member variables:
        try:
            self.__dictionary_chat_room_participants = {}
            self.__dictionary_client_current_state = {}
            self.__dictionary_clients_choices = {}
            self.__list_all_active_sockets = []
            self.__server_port_number = 8181
            self.__server_ip_address = "localhost"
            self.__server_keep_running = True
            self.__MAX_CLIENTS = 100
            self.__MAX_BUFFER_LENGTH = 1024
            

            # Create socket:
            self.__server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

            # Set server socket to be non-blocking:
            self.__server_socket.setblocking(False)

            # Set socket option to keep it alive:
            self.__server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)

            # Bind socket to the address and port:
            self.__server_socket.bind((self.__server_ip_address,self.__server_port_number))           

            # Print confirmation dialog:
            print("Done initializing chat server. Server is ready to run...")


        except Exception as e:

            # Print dialog:
            print("[Exception] Caught exception during server initialization. Details: ",e)

            # If not None, close server socket:
            if self.__server_socket != None:
                
                # Close socket:
                self.__server_socket.close()

                # Print confirmation:
                print("Closed server socket.")
            
            # Exit program with code -1:
            print("Exiting program...")
            sys.exit(-1)


    # ------------------------------------ Class Private Member Functions --------------------------

    def __mainEventHandler(self):

        '''
            Private member function to handle the
            main events on the running server.       
        
        '''

        # Print dialog:
        print("Chat server running on TCP port ", self.__server_port_number)

        # Set the server socekt to listen mode for incloming client connection requests:
        self.__server_socket.listen(self.__MAX_CLIENTS)
        
        # Append server socket to the list of active sockets:
        self.__list_all_active_sockets.append(self.__server_socket)


        # Enter the main event loop:
        while(self.__server_keep_running == True):

            try:

                # Monitor the sockets for event and obtain 
                # the source(s) of the event(s):
                event_source_list,ignore_this,ignore_this = select(self.__list_all_active_sockets,[],[],None)   
 

                # Check who the source of the event 
                # is and handle event accordingly:
                for source in event_source_list:                    

                    # If source is the server socket:
                    if source == self.__server_socket:                       
                        
                        # Handle new client connection request:
                        self.__handleNewClientRequest()
                    
                    # The source is a connected client 
                    else:
                        
                        # Handle a connected client:
                        self.__handleConnectedClient(source)
            
            except KeyboardInterrupt:

                # Call the handler function:
                self.__signal_handler()


        # Clean up resources:
        self.__doPostStopCleanup()

    def __handleNewClientRequest(self):

        '''
            Private member function for handling
            incoming new client connection 
            requests.
        
        '''

        # Initialize the client socket:
        accepted_client_socket = None

        try:

            # Initialize clients status:
            clients_current_status = None
        
            # Accept the connection request 
            # from the new client:
            accepted_client_socket,accepted_client_address = self.__server_socket.accept()

            # Get client's ip address and port number:
            clients_ip = str(accepted_client_socket.getpeername()[0])
            clients_port = str(accepted_client_socket.getpeername()[1]) 

            # Get this client's current 
            # status from the dictionary:
            clients_current_status = self.__getClientsCurrentStatus(clients_ip,clients_port) # (ip,port)

            
            # At this point, the client 
            # should not exist in the 
            # dictionary:
            if clients_current_status != None:

                # Send an error message to client:
                accepted_client_socket.send("Error in joining the server. Invalid client status.".encode('UTF-8'))

                # Close socket:
                accepted_client_socket.close()

                # Return:
                return


            # Set as non-blocking:
            accepted_client_socket.setblocking(False)

            # Set socket to be kept alive:
            accepted_client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)

            # Send the welcome message and ask for user id:
            message_to_client = "Welcome! Please enter your user id to continue."
            self.__sendMessageToAClient(accepted_client_socket,message_to_client)

            # Change client's current status to zero(0):
            clients_current_status = 0
            self.__dictionary_client_current_state[(clients_ip,clients_port)] = clients_current_status

            # Add this socket to the list of active sockets:
            self.__list_all_active_sockets.append(accepted_client_socket)

            print("New client connected from IP address: ",clients_ip," Port#: ", clients_port)

        
        except Exception as e:

            # Print dialog:
            print("[Exception] Caught an exception while handling a new client request. Details: ", e)

            # If the client status was changed, 
            # delete that entry from dictionary:
            if clients_current_status == 0:

                # Delete entry:
                del self.__dictionary_client_current_state[(clients_ip,clients_port)]

            
            # Close socket:
            if accepted_client_socket:
                
                # Close:
                accepted_client_socket.close()

                # Remove from list of active sockets:
                self.__list_all_active_sockets.remove(accepted_client_socket)
                
                # Print dialog:
                print("Closed accepted socket.")
            
            # Return:
            return

    def __handleConnectedClient(self,client_socket):

        '''
            Handle an already connected client.

        '''

        try:
            
            # Get this client's ip address and port number:
            clients_ip = str(client_socket.getpeername()[0])
            clients_port = str(client_socket.getpeername()[1])            


            # Get clients current status:
            clients_current_status = None
            clients_current_status = self.__getClientsCurrentStatus(clients_ip,clients_port)


            # At this point, client should have a valid status. 
            # If not, raise an exception:
            if clients_current_status == None:
                raise Exception("Invalid client status.")

            # If client staus is 0:
            elif clients_current_status == 0:

                # Handle user id from client:
                self.__handleUserIdFromClient(client_socket)

            # If client status is 1:
            elif clients_current_status == 1:

                # Handle choice about creating/joining a chatroom:
                self.__handleJoinChoice(client_socket)

            # If client status is 2:
            elif clients_current_status == 2:

                # Handle chat room name choice from user:
                self.__handleChatRoomNameChoice(client_socket)

            # If client status is 3: // client is connected and in a chat room:
            elif clients_current_status == 3:

                # Read client message and 
                # handle accordingly:
                self.__readAndHandleClientMessage(client_socket)


        except Exception as e:

            # Print dialog:
            print("[Exception] Caught an exception while handling a connected client. Details: ",e)

            # Return:
            return

    # *******************

    def __handleUserIdFromClient(self,client_socket):

        '''
            Reads, validates, and stores user id
            sent by the client.
        '''

        try:

            # Read the message from the socket:
            read_message = self.__readMessageFromSocket(client_socket)

            # The message should be a valid user id (e.g., non-empty string):
            if(read_message == None):

                # Message client:
                self.__sendMessageToAClient(client_socket,"Could not read user id. Please try again.")

                # Return:
                return

            # Check if the user id is a valid string:
            valid_user_id = self.__isValidUserId(read_message)

            # If not a valid user id, inform client:
            if not(valid_user_id):

                # Send message:
                self.__sendMessageToAClient(client_socket,"Invalid user id. Please retry.")

                # Return:
                return

            # Otherwise, send join instruction and accept this user id:
            else:

                # Send join instruction:
                join_instruction = "Hi, " + str(read_message) + "! Enter 1 or 2 for - (1) Create and Join a Chat Room (2) Join an Existing Chat Room."
                
                #client_socket.send(join_instruction.encode('UTF-8'))
                self.__sendMessageToAClient(client_socket,join_instruction)

                # Change client's current status:
                clients_ip = str(client_socket.getpeername()[0])
                clients_port = str(client_socket.getpeername()[1])

                current_status = 1
                self.__dictionary_client_current_state[(clients_ip,clients_port)] = current_status # Join instruction sent, accepted user id                

                # Store user id in the dictionary:
                self.__dictionary_clients_choices[(clients_ip,clients_port)] = [None]*3 # Creating and assigning a list of length 3
                self.__dictionary_clients_choices[(clients_ip,clients_port)][0] = str(read_message) # Saving user id

                # Return:
                return               

        except Exception as e:

            # Print dialog:
            print("[Exception] Caught an exception in handling user id. Details: ",e)

            # Return:
            return

    def __readMessageFromSocket(self,source_socket):

        '''
            Reads the message from the source socket
            and returns the message to the caller.

        '''

        try:

            # Initialize variable:
            read_message = None

            # Read from socket:
            read_message = source_socket.recv(self.__MAX_BUFFER_LENGTH).decode('UTF-8').strip()

            # Return message:
            return read_message

        except Exception as e:

            # Print dialog:
            print("[Exception] Error in reading message from given socket. Details: ",e)

            # Return None:
            return None

    def __isValidUserId(self,user_id):

        '''

            Returns true only if the user_id string
            is not empty, newline, or 
            carriage return+newline.


        '''

        # String is not empty:
        condition_1 = (len(user_id) > 0)

        # String is not a newline:
        condition_2 = (user_id != "\n" or user_id != '\n')

        # String is not CR + LF:
        condition_3 = (user_id != "\r\n" or user_id != '\r\n')

        # Return:
        return condition_1 and condition_2 and condition_3


    # ******************
    def __handleJoinChoice(self,client_socket):

        '''
            Handles the join choice
            from the client.
        '''

        try:
            
            # Read the message from the socket:
            read_message = self.__readMessageFromSocket(client_socket)

            # The message should be a valid user id (e.g., non-empty string):
            if(read_message == None):

                # Message client:
                self.__sendMessageToAClient(client_socket,"Could not read your join choice. Please try again.")

                # Return:
                return

            # If choice is not valid, inform client:
            if(not(self.__isValidJoinChoice(read_message))):

                # Inform client:
                self.__sendMessageToAClient(client_socket,"Invalid join choice. Please retry.")

                # Return:
                return

            # Otherwise, proceed:
            else:

                 # Get this client's ip address and port number:
                 clients_ip = str(client_socket.getpeername()[0])
                 clients_port = str(client_socket.getpeername()[1])

                 # Change client's current state:
                 self.__dictionary_client_current_state[(clients_ip,clients_port)] = 2 # Client has made a join choice:

                 # Store client's join choice:
                 self.__dictionary_clients_choices[(clients_ip,clients_port)][1] = str(read_message)

                
                 # If client chose (1) Create and Join a Chat Room:
                 if read_message == "1":

                     # Instruct client:
                     self.__sendMessageToAClient(client_socket,"Enter a chat room name to create and join.")
 
                     # Return:
                     return

                 # Else, client chose (2) Join an Existing Chat Room
                 else:

                     # If there are currently 
                     # no chat room, inform user
                     # and ask for a chat room name
                     # to create and join the room:
                     if(not(self.__IsAnyChatroomAvailable())):
 
                         # Inform:
                         self.__sendMessageToAClient(client_socket,"Currently no chat room available. Enter a chat room name to create and join the room.")

                         # Return:
                         return

                     # Otherwise, send a list of available
                     # chat room names and ask user to
                     # choose one:
                     else:

                         # Get a list of chat room names:
                         available_chat_rooms = self.__getAvailableChatroomNames()
 
                         # Inform client:
                         self.__sendMessageToAClient(client_socket,"Available chat rooms: " + available_chat_rooms + "Enter a chat room name to join.")
 
                         # Return:
                         return
 
        except Exception as e:
 
            # Print dialog:
            print("[Exception] Caught an exception while handling join choice. Details: ",e)

    def __isValidJoinChoice(self,join_choice):

        '''
            Returns true only when
            join choice is either "1"
            or "2".

        '''

        condition_1 = (len(join_choice) > 0)
        condition_2 = (join_choice == "1")
        condition_3 = (join_choice == "2")

        result = condition_1 and (condition_2 or condition_3)

        return result

    def __getClientsCurrentStatus(self,str_client_ip,str_client_port):

        '''
            Returns the status number (i.e., None, 0, 1, 2, or 3)
            of the client inidicated by the ip address and port.

        '''

        try:

            # See if the client exists in 
            # the dictionary:
            clients_current_status = self.__dictionary_client_current_state[(str_client_ip,str_client_port)]

            # Return status:
            return clients_current_status

        # The client does not exist in 
        # the dictionary yet. 
        # It's a new client:
        except KeyError as e:

            # Return None:
            return None

    def __IsAnyChatroomAvailable(self):

        '''
            Checks the dictionary and returns
            False if there are no chat rooms
            available for a user to join. 
            
            Returns True otherwise.      
        
        '''

        # If the dictionary is empty, return False:
        if len(self.__dictionary_chat_room_participants) == 0:
            return False
        
        # Dictionary not empty. Return True:
        else:
            return True

    def __getAvailableChatroomNames(self):

        '''
            Return a string of chat room names
            that are available for a client
            to join.        
        
        '''

        # Initialize the list to reutrn to:
        list_chat_room_names = list(self.__dictionary_chat_room_participants.keys())

        # Convert to string:
        available_rooms = ""
        for item in list_chat_room_names:
            available_rooms += str(item) + "\n"

        # Return:
        return available_rooms
     
    # *****************

    def __handleChatRoomNameChoice(self,client_socket):

        '''
            Reads and handles the chat room
            name from client socket.

        '''

        try:

            # Read the chat room name from the socket:
            chat_room_name_chosen = self.__readMessageFromSocket(client_socket)

            # If invlaid chat room name string (empty or \n or \r\n) 
            # given, inform user:
            if(not(self.__isChatRoomNameValid(chat_room_name_chosen))):

                # Inform client:
                self.__sendMessageToAClient(client_socket,"Chat room name cannot be an empty string. Please retry.")

                # Return:
                return

            # Check this client's join choice:
            clients_ip = str(client_socket.getpeername()[0])
            clients_port = str(client_socket.getpeername()[1])
            clients_join_choice = self.__dictionary_clients_choices[(clients_ip,clients_port)][1] # Index 1 = Join Choice


            # If client's join choice was "1" (Create and Join Chat Room)
            if clients_join_choice == "1":

                # DO NOT create the chat room if a chat 
                # room with the same name already 
                # exists:
                if(self.__doesChosenChatroomExist(chat_room_name_chosen) == True):

                    # Inform client:
                    self.__sendMessageToAClient(client_socket,"A chat room with this same name already exists. Please retry with a different name for the chat room you want to create.")

                    # Return:
                    return


                # Get client's user id:
                clients_user_id = self.__dictionary_clients_choices[(clients_ip,clients_port)][0] # Index 0 = User Id

                # Create an entry in chat room dictionary:
                self.__dictionary_chat_room_participants[chat_room_name_chosen] = [(client_socket,clients_user_id)]

                # Change client's state:
                self.__dictionary_client_current_state[(clients_ip,clients_port)] = 3 # Client has provided chat room name and joined it

                # Update clients choice:
                self.__dictionary_clients_choices[(clients_ip,clients_port)] = str(chat_room_name_chosen)

                # Inform client:
                confirmation_message = "Successfully joined chat room " + str(chat_room_name_chosen) + ". Happy chatting!"
                self.__sendMessageToAClient(client_socket,confirmation_message)

                # Return:
                return

            # Client's join choice was "2"(Join an Existing Chat Room)
            else:

                # If no chat room available, create a 
                # chat room and add client to the room:
                if(self.__IsAnyChatroomAvailable() == False):

                    # Get client's user id:
                    clients_user_id = self.__dictionary_clients_choices[(clients_ip,clients_port)][0] # Index 0 = User Id

                    # Create an entry in chat room dictionary:
                    self.__dictionary_chat_room_participants[chat_room_name_chosen] = [(client_socket,clients_user_id)]

                    # Change client's state:
                    self.__dictionary_client_current_state[(clients_ip,clients_port)] = 3 # Client has provided chat room name and joined it

                    # Update clients choice:
                    self.__dictionary_clients_choices[(clients_ip,clients_port)] = str(chat_room_name_chosen)

                    # Inform client:
                    confirmation_message = "Successfully joined chat room " + str(chat_room_name_chosen) + ". Happy chatting!"
                    self.__sendMessageToAClient(client_socket,confirmation_message)

                    # Return:
                    return

                # Else, there are chat room available:
                else:

                    # If chosen chat room is not available, inform user:
                    if(not(self.__doesChosenChatroomExist(chat_room_name_chosen))):

                        # Inform:
                        self.__sendMessageToAClient(client_socket,"Chosen chat room is not available. Please retry.")

                        # Return:
                        return

                    # Otherwise, add client to this room:
                    else:

                        # Get client's user id:
                        clients_user_id = self.__dictionary_clients_choices[(clients_ip,clients_port)][0] # Index 0 = User Id

                        # Add client to chat room:
                        self.__dictionary_chat_room_participants[chat_room_name_chosen].append((client_socket,clients_user_id))

                        # Change client state:
                        self.__dictionary_client_current_state[(clients_ip,clients_port)] = 3 # Client has provided chat room name and joined it

                        # Inform client:
                        confirmation_message = "Successfully joined chat room " + str(chat_room_name_chosen) + ". Happy chatting!"
                        self.__sendMessageToAClient(client_socket,confirmation_message)

                        # Return:
                        return            


        except Exception as e:

            # Print dialog:
            print("[Exception] Caught an exception while handling chat rrom name choice. Details: ",e)

            # Return:
            return

    def __isChatRoomNameValid(self,chosen_chat_room):

        '''

            Returns true only if the given string
            is not empty, newline, or 
            carriage return+newline.


        '''

        # String is not empty:
        condition_1 = (len(chosen_chat_room) > 0)

        # String is not a newline:
        condition_2 = (chosen_chat_room != "\n" or chosen_chat_room != '\n')

        # String is not CR + LF:
        condition_3 = (chosen_chat_room != "\r\n" or chosen_chat_room != '\r\n')

        # Return:
        return condition_1 and condition_2 and condition_3

    def __getAvailableChatroomNameList(self):

        '''
            Returns a list of all available
            chat room names.

        '''

        # Initialize the list to reutrn to:
        list_chat_room_names = list(self.__dictionary_chat_room_participants.keys())

        # Return:
        return list_chat_room_names

    def __doesChosenChatroomExist(self,chosen_chat_room):

        '''
            Returns true only if the the chosen
            chat room exists on the server.
        '''

        # Get a list of all available chat room names:
        list_available_chat_rooms = self.__getAvailableChatroomNameList()

        # Initialize result:
        chat_room_exist = False
        for room_name in list_available_chat_rooms:
            if room_name == chosen_chat_room:
                chat_room_exist = True
                break

        # Return:
        return chat_room_exist


    # ***************

    def __readAndHandleClientMessage(self,client_socket):

        '''
            Reads message sent by a client and
            handles it accordingly.        

        '''

        try:

            # Read the message from client:
            client_message = self.__readMessageFromSocket(client_socket)


            #If empty message, ignore:
            if client_message == "":
                pass                


            # If message is CLOSE, initiate closing
            # the connection:
            elif client_message == "CLOSE":

                # Initiate closing:
                self.__initiateCloseSequence(client_socket)

                # Return:
                return

            # Non-empty message. Relay to others 
            # in the chat room
            else:

                # Call function:
                self.__relayMessageToChatroomParticipants(client_socket,client_message)

                # Return:
                return

            
        except Exception as e:

            # Print dialog:
            print("[Exception] Caught an exception while reading and handling client message. Details: ",e)

            # Return:
            return


    def __relayMessageToChatroomParticipants(self,client_socket,client_message):

            '''

                Relay message recevied from the client
                to the other members of the chatroom.

            '''

            try:


                # Get this client's chat room name and user id:
                client_chat_room_name, client_user_id = self.__getConnectedClientsChatroomNameAndUserId(client_socket)

                # Prepare the relay message:
                relay_message = client_user_id + ": " + client_message

                # Get a list of tuples of all client 
                # who are member of the same 
                # chat room:
                list_chat_room_member_tuples = self.__dictionary_chat_room_participants[client_chat_room_name]


                # Iterate through the list
                # and relay the message:
                for tuple_item in list_chat_room_member_tuples:

                    # Get the socket:
                    current_socket = tuple_item[0]

                    # Relay to all except source socket:
                    if current_socket != client_socket:

                        # Send message:
                        self.__sendMessageToAClient(current_socket,relay_message)

                # Done. Return:
                return


            except Exception as e:

                # Print dialog:
                print("[Exception] Caught an exception while relaying client message. Details: ",e)

                # Return:
                return

    # ********************
    def __initiateCloseSequence(self,client_socket):

        '''
            Initiate the sequence of events 
            for handling the special "CLOSE" 
            message from the client.       
        
        '''

        try:
                   
            
            # Get this client's chat room name and user id:
            client_chat_room_name, client_user_id = self.__getConnectedClientsChatroomNameAndUserId(client_socket)

            # Remove this client from the chat room:
            self.__dictionary_chat_room_participants[client_chat_room_name].remove((client_socket,client_user_id))

            # Remove the client socket from the list of active sockets:
            self.__list_all_active_sockets.remove(client_socket)

            # Remove this client socket from dictionary of client states and client choices:
            clients_ip = str(client_socket.getpeername()[0])
            clients_port = str(client_socket.getpeername()[1])
            del self.__dictionary_client_current_state[(clients_ip,clients_port)]
            del self.__dictionary_clients_choices[(clients_ip,clients_port)]

            # Print dialog:
            print("User ",client_user_id," has left chat room ", client_chat_room_name)

            # Close connection:
            if client_socket:

                # Close:
                client_socket.close()     

            


        except Exception as e:

            # Print dialog:
            print("[Exception] Caught an exception in handling the CLOSE sequence. Details: ",e)
  
    def __getConnectedClientsChatroomNameAndUserId(self,client_socket):

        '''
            Returns the name of the chat 
            room the client socket is 
            part of.       
        
        '''

        # Initialize variables:
        result_chat_room_name = None
        result_user_id = None

        # Iterate through the dictionary of 
        # chat room names and client 
        # sockets, user ids:
        for chat_room_name,list_tuple_socket_user_id in self.__dictionary_chat_room_participants.items():

            # Iterate through the list of tuples and search:
            for item in list_tuple_socket_user_id:

                # If the socket and client socket 
                # are the same, done searching. 
                if(item[0] == client_socket):

                    # Update result chat room name and user id:
                    result_chat_room_name = chat_room_name
                    result_user_id = item[1]

                    # Return:
                    return result_chat_room_name,result_user_id
        
        # Return:
        return result_chat_room_name,result_user_id # This will return None

    def __signal_handler(self):

        # Set server keep running flag to False:
        self.__server_keep_running = False

        # Print dialog:
        print("\nCtrl+C pressed. Chat server has been shut down.")

    def __doPostStopCleanup(self):

        '''
            Closes server socket and deletes 
            member variables.
        
        '''

        try:
            
            # Close server socket:
            if self.__server_socket:
                self.__server_socket.close()
            
            # Delete dictionary and list members:
            del self.__dictionary_chat_room_participants
            del self.__list_all_active_sockets

        except Exception as e:

            # Print dialog:
            print("[Exception] Caught exception during post stop cleaning. Details: ",e)
            # Exit program:
            sys.exit(-1)

    # *******************
    def __sendMessageToAClient(self,client_socket,str_message_to_send):

        '''
            Safely sends all of the given message
            to the client over the non-blocking
            socket.        
        '''

        

        # Encode data:
        encoded_message = str_message_to_send.encode('UTF-8')

        # Initialize total sent amount:
        total_data_sent = 0

        # Keep sending until all data
        # has been transmitted:
        while(total_data_sent < len(encoded_message)):

            try:

                # Send data:
                number_of_bytes_sent = client_socket.send(encoded_message[total_data_sent:])

                # If no data was sent, raise exception:
                if(number_of_bytes_sent == 0):

                    # Raise exception:
                    raise Exception("Unable to send data. Connection closed by remote peer.")

                # Update total data sent:
                total_data_sent += number_of_bytes_sent

            # Ignore any BlockingIOError:
            except BlockingIOError:

                # Continue to retry sending:
                continue 

    

    # ------------------------------------ Class Public Member Functions ---------------------------
    def run_server(self):

        # Show confirmation dialog:
        print("Running chat server program...")

        # -------- Necessary Function Calls ------------
        self.__mainEventHandler()

# *********************************** Main Function **************************************************
def main():

    # Create a ChatServer object:
    chat_server = ChatServer()

    # Start running the chat server:
    chat_server.run_server()


if __name__ == "__main__":
    main()


