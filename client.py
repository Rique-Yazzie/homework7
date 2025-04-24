'''
	
	CS460(Spring-2025)	
	Homework-3: Client program for the text-based 
						 chat application.
	Author:
		Nazmul(mh2752@nau.edu)

'''

import socket
from select import select
import sys


# ----------------------------------------------------- Main Function ---------------------------------------------------
def main():


	# Display message about starting the client application:
	print("Starting chat client...")

	
	# Get the chat server's IP address as input from the user:
	server_ip = None
	# Prompt for server IP address:
	server_ip = input("Enter chat server's IP address: ")

	# Chat server application listens on port 8181:
	server_port = 8181


	# Maximum size of the buffer in bytes:
	MAX_BUFFER_SIZE = 1024


	# Create a TCP socket and connect 
	# to the chat server:
	try:

		# Create socket:
		client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

		# Set socket to non-blocking:
		client_socket.setblocking(False)

		# Set socket option to keep the connection alive:
		client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)

		# Connect to server:
		try:
			client_socket.connect((server_ip,server_port))
		
		except BlockingIOError as e:

			print("Handled a BlockingIOError. Proceeding normally.")


		# Print confirmation:
		print("Connected to chat server at IP address = ", server_ip, " PORT# = ",server_port)


		# The program needs to concurrently monitor keyboard events (sys.stdin) for inputs from 
		# user and also the socket to receive messages relayed from the server:
		event_sources_to_monitor = [sys.stdin, client_socket]


		# Flag variable to continue/stop monitoring 
		# for user inputs/ server messages:
		continue_event_monitoring = True

		# Enter the main event monitoring loop:
		while(continue_event_monitoring == True):

			# Monitor and obtain the source of the event:
			event_source_list,ignore_this,ignore_this = select(event_sources_to_monitor,[],[],None)
			
			# Check who is the source of 
			# the event and handle event 
			# accordingly:
			for source in event_source_list:

				# If the source is the keyboard, 
				# it's a user-input event:
				if source == sys.stdin:

					# Get the keyboard input from the user:
					user_input = sys.stdin.readline().strip()					

					# If input is "CLOSE", send CLOSE message to the 
					# server and then shutdown the socket and 
					# exit the event loop:
					if user_input == "CLOSE":

						# Send message to server:					
						sendMessageToAClient(client_socket,user_input)

						# Close socket:
						client_socket.close()

						# Set event monitoring flag to False:
						continue_event_monitoring = False
					
					# Anything other than 'CLOSE' should 
					# be sent to the server:
					else:

						# Send message to server:
						sendMessageToAClient(client_socket,user_input)

				# The source is the socket. The server sent 
				# something for the client:
				else:

					# Read from the socket:
					server_message = client_socket.recv(MAX_BUFFER_SIZE).decode('UTF-8').strip()

					# Display non-empty messages only:
					if server_message != "":
						# Display message:
						print("\n>>> ", server_message)


	except Exception as e:

		# Show message:
		print("[Exception] Caught exception in creating and connecting socket. Details: ", e)

		# Close socket to release system resources:
		client_socket.close()

		# Print confirmation:
		print("Closed socket...")

		# Exit program:
		print("Exiting program...")
		sys.exit(-1)

# ------------------------------------------- Helper Function(s) ---------------------------------------------------------

def sendMessageToAClient(client_socket,str_message_to_send):

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

# -------------------------------------------------- Run Main ----------------------------------------------------------
if __name__ == "__main__":
	main()







