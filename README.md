# mist_backup_maps
This script will download a site's AP pictures and maps from your Mist deployment and also create a new map with the AP(s) located on the downloaded maps. This is helpful since you cannot natively export this information from the Mist dashboard.

After cloning this repository, you will need to install the required Python modules by running `pip install -r requirements.txt`.

To make things easier, you can also create another file called `.env` in the repository folder and create the following variables below with Mist information assigned to them. If you do not complete this step, the script will prompt you for the required information.
* MIST_API_TOKEN (ex. **MIST_API_TOKEN=RANDOM_STRING_OF_CHARACTERS**)
* MIST_ORG_ID (ex. **MIST_ORG_ID=RANDOM_STRING_OF_CHARACTERS**)

A new directory with the site's name will be created in the repository folder along with sub-directories that contain pictures of the APs (if present) and pictures of your maps (if present) respectively. A CSV with a timestamp of the date that you run the script will also be created in the main directory. That CSV will contain the raw data for the AP(s) positioning on the map(s).
