.PHONY: clean

ifdef LEPHAREDIR
LEPHARE_DIR := $(LEPHAREDIR)
else
LEPHARE_DIR := $(HOME)/Library/Caches/lephare
endif

FILES := file1.txt file2.log file3.tmp

lephare_full_clean:
	rm -rf $(LEPHARE_DIR)/

roman_data_clean:
	rm -rf $(LEPHARE_DIR)/data/filt/roman

clean:
	for file in $(FILES); do \
		rm -f $$file; \
	done
