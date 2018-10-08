# Google Drive ppapadop@UCI Public Access software sources
SURL=https://googledrive.com/host/1L-VOgFEvE3OVVQYT3Okfu7Fy9MLUcr8W
DOWNLOADER=/opt/rocks/share/devel/bin/get_sources.sh

download: sources
	SURL=$(SURL) $(DOWNLOADER)

sources:
	mkdir sources
	

