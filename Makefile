.PHONY: doctor book html pdf chapter refresh preview clean deploy

doctor:            ## check toolchain + show which series resolve live
	python scripts/doctor.py

book:              ## all formats
	quarto render

html:
	quarto render --to html

pdf:
	quarto render --to pdf

chapter:           ## make chapter CH=01-introduction
	quarto render chapters/$(CH).qmd --to html

refresh:           ## force a full re-fetch, then render
	rm -rf _freeze .jupyter_cache
	python -c "from pylib.datafeeds import refresh_all; refresh_all()"
	quarto render

preview:
	quarto preview

clean:
	rm -rf _output _freeze .quarto

deploy:
	quarto publish gh-pages --no-prompt
