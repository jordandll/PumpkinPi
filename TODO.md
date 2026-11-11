Use the following prompt to update the phone app according to the changes made on the server end.

--- Begin Prompt ---

The server this phone app talks to has been updated so that it accords with a protocol that allows for a list of commands to be sent in one network request; If the server recieves more than one command in a request, it parses and then executes them in sequencial order.  Moreover, it now can now process requests even while it is executing commands from a previous one.  The server continues accepting `monitor` requests while a command batch is running.
Other command batches received during execution are queued in order, and their clients
receive a warning that the server is busy.  That warning message is: 'WARNING: Server is busy; commands have been queued.'.

Can you update this phone app so that it may notify the user if it recieves such a warning?

--- End Prompt ---
