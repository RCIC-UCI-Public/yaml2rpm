# Google Drive ppapadop@UCI Public Access software sources
SURL=https://googledrive.com/host/1L-VOgFEvE3OVVQYT3Okfu7Fy9MLUcr8W
ROCKSSHARE=/opt/rocks/share/devel
DOWNLOADER=$(ROCKSSHARE)/bin/get_sources.sh

include  $(ROCKSSHARE)/src/roll/etc/Rules-repo-centos.mk
download: sources
	SURL=$(SURL) $(DOWNLOADER)
sources:
	mkdir sources

cleansources:
	- /bin/rm -rf sources

veryclean: clean cleansources
	make -C yamlspecs veryclean	

