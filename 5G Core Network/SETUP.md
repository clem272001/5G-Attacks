1. Run the script. It should take you from cloning the repo to having all pods up and running. 
This script will install some prerequisite packages. If you wish to install them manually, comment out lines 14-18.

--------------------------

2. If all went well, when the script finishes you should see all pods are running. You will also see a reported port for the mongodb webui.

--------------------------

3. You can now try visiting http://192.168.57.2:[webui_port] and login with the admin credentials. 

--------------------------

4. Go to [this file](https://github.com/aligungr/UERANSIM/blob/master/config/open5gs-ue.yaml) and copy its contents.
Create a file called ```ue.yaml``` in the ```5G Core Network/User_equipments/```' directory and paste the copied file contents. No changes are required.

--------------------------

5. You can now run the ```create_ue_conf.sh``` script with no problems.

--------------------------

6. Next up, you will need to make some changes in the file ```add_subscribers_open5gs_mongodb.py```.
There was a bug where users would get created with a 14-digit instead of a 15-digit imsi. 
Replace line 33 with the following code:                                                                                                                                                                                  
```"imsi": "999700000000" + str(nbr_sub).zfill(3)```

--------------------------

7. You should now be able to run the ```add_subscribers_open5gs_mongodb.py```. You will have to run it from inside the master node.
If you don't want to do that, you can expose the mongodb service to NodePort and change the database IP address and port in the script. 
If you do this, make sure to delete the NodePort service afterwards!!!

--------------------------

8. SSH into the master node and check the logs of the ue pod and the gnb pod. Verify they are operational.  
