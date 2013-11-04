#!/usr/bin/python
# Rostislav Tsiomenko
# tsiomr1@umbc.edu
# Scrape Los Angeles Municipal Code
import urllib2
import re
base_url = "https://raw.github.com/opengovfoundation/losangeles-city-code/master/Municipal/"
chapters = 19
first_chapter = 1
# Chapters that do not exist
dne = [14]

# Remove some tags that get into titles
def sanitize(str):
    sanitized = re.sub(r'<span class="Apple-converted-space">(.*)</span>', "", str, re.DOTALL)
    return re.sub(r'\.342\.\)', "", sanitized)

# Don't write XML like this
def write_xml(division, chapter_number, chapter_title, section_number, section_title, text, history):
    division_dict = {"1":"General Provisions and Zoning", 
                     "2":"Licenses, Permits, Business Regulations", 
                     "3":"Public Health Code", 
                     "4":"Public Welfare", 
                     "5":"Public Safety and Protection",
                     "6":"Public Works and Property", 
                     "7":"Transporation", 
                     "8":"Traffic", 
                     "9":"Building Regulations", 
                     "10":"Business Regulations", 
                     "11":"Noise Regulation", 
                     "12":"The Water Conservation Plan of the City of Los Angeles", 
                     "13":"The Emergency Energy Curtailment Plan of the City of Los Angeles", 
                     "15":"Rent Stabilization Ordinance", 
                     "16":"Housing Regulations",
                     "17":"Rules and Regulations Governing the Use of the Los Angeles Airports",
                     "18":"Grocery Worker Retention Ordinance", 
                     "19":"Environmental Protection"}
    filename = "statedecoded-master/htdocs/admin/import-data/" + section_number.rstrip('.') + ".xml"
    # Build orderby string, remember subsections (i.e. 1.456.6)
    orderby = section_number.rstrip('.').partition('.')[2]
    # TODO: figure out a better way than rstrip()ing everything
    law = open(filename, "w")
    law.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
    law.write("<law>\n")
    law.write("\t<structure>\n")
    law.write("\t\t<unit label=\"chapter\" identifier=\"" + division + "\" order_by=\"" + division_dict[division] + "\" level=\"1\">")
    law.write(division_dict[division] + "</unit>\n")
    law.write("\t\t<unit label=\"article\" identifier=\"" + chapter_number + "\" order_by=\"" + chapter_number + "\" level=\"2\">")
    law.write(chapter_title + "</unit>\n")
    law.write("\t</structure>\n")
    law.write("\t<section_number>" + section_number.rstrip('.') + "</section_number>\n")
    law.write("\t<catch_line>" + section_title + "</catch_line>\n")
    law.write("\t<order_by>" + orderby + "</order_by>\n")
    law.write("\t<text>")
    text = text.lstrip().rstrip()
    law.write(text)
    law.write("\n\t</text>\n")
    if history:
        law.write("\t<history>" + history + "</history>\n")
    law.write("</law>\n")
    law.close()
    # Debug code:
    # print filename
    # print division_dict[division]
    # print "Chapter " + chapter_number
    # print chapter_title
    # print "Section " + section_number
    # print section_title
    # print text
    # print "\n\n========"

for chapter in range (first_chapter,chapters+1):
    # 3, 8, 12, 13, 17 do not have articles or have roman numerals
    if chapter not in dne:
        url = base_url + ("chapter0" if (chapter < 10) else "chapter") + str(chapter) + ".html"
        html = urllib2.urlopen(url).read()
        articles = re.split(r'(>ARTICLE [\d\.]{1,6})', html, 0, re.DOTALL)
        # Delete everything that comes before Chapter 1
        del (articles[0])
        for x in range(0, len(articles), 2):
            print chapter
            article_num = articles[x]
            article_text = articles[x+1]
            try:
                article_title = sanitize(re.match(r'<br>(.*?)</p>', article_text, re.DOTALL).group(1)).replace("<br>", "")
            except:
                #print "Shit just went wack, you might want to check it out!"
                #print "In chapter " + str(chapter)
                #print "Article *" + article_num
                division_suffix = re.match(r', DIVISION (.*?)<br>', article_text).group(1)
                article_num = article_num + "." + division_suffix
                article_title = re.match(r'(.*?)]</p>', article_text, re.DOTALL).group(1).partition('[')[2]
                #print "New article number: " + article_num
                #print "New article title: " + article_title

            sections = re.split(r'<p class=.{4,7}<b>(SEC. [\d\.]{1,10})', article_text, 0, re.DOTALL)
            del (sections[0])
            for y in range (0, len(sections), 2):
                section_num = sections[y]
                section_text = sections[y+1]
                section_title = ""
                try:
                    section_title = sanitize(re.search(r'</span>(.*?)</b>', section_text).group(1)).lower().title()
                except AttributeError:
                    # Some sections are untitled and the regex will fail
                    section_title = "No title"
                    print "No title for section " + section_num

                # Get law text by stripping the section title, HTML tags, and whitespace
                try:
                    content = re.sub(section_title,"", (re.sub(r'<[^<]+?>','',section_text)), 1).rstrip()
                except:
                    # This should never get called anymore
                    print "==Something went wrong with stripping law text!=="
                    print section_num
                    print section_title
                    exit()

                # Write XML
                chapter_xml = str(chapter)
                # Replace CHAPTER X with just X
                article_xml = re.sub('>ARTICLE ','',article_num)
                # Remove silly brackets, make capitalization sane
                atitle_xml = re.sub('[\[\]]','',article_title.lstrip().lower().title())
                # Make Sec. X.XX just X.XX
                section_xml = re.sub('SEC. ','',section_num).lower().title()
                # Remove more silly brackets
                stitle_xml = re.sub('[\[\]]','',section_title)
                # Remove the article TOC that sometimes appears
                content_xml = re.sub('DIVISION.*', '', content, 0, re.DOTALL).replace("BASIC PROVISIONS.", "").replace("<p class=\"p10\"", "")
                # Parse history section within content
                try:
                    history_xml = re.search(r'SECTION HISTORY\s(.*)', content_xml, re.DOTALL).group(1)
                    print history_xml
                    content_xml = re.sub(r'SECTION HISTORY\s.*', '', content_xml, 0, re.DOTALL)
                except AttributeError:
                    history_xml = False
                if (chapter == 8):
                    print chapter_xml, article_xml, stitle_xml
                write_xml(chapter_xml, article_xml, atitle_xml, section_xml, stitle_xml, content_xml, history_xml)
