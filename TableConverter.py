import os
import re as RegEx


#=============================================================
# Load a file, look for tables, if any are found, change them to SimpleTable format and return the result
def ProcessFile(filename):
    if not os.path.exists(filename):
        raise(ValueError, "ProcessFile: Can't open file '"+filename+"'")

    # Read the file
    with open(filename) as file:
        source=file.readlines()

    # A table starts with a line that begins "||"
    # It continues until there's a line that does *not* begin with "||"
    # (Remember that lines can be continued by ending them with " _")
    out=[]
    table=[]
    line=""
    inTable=False
    prevLineContinues=False
    for line in source:
        if line[-1:] == "\n":
            line=line[:-1]  # Drop the trailing "\n"

        # A line which follows a line ending with space-underscore will be handled the same way as the last line.  It can never begin or end a table.
        if prevLineContinues:
            if line.endswith(" _"):
                prevLineContinues=True
                print("remove ' _' from:   "+line)
                line=line[:-2]
            else:
                prevLineContinues=False
            if inTable:
                table.append(line)
                print("another continued row line:   "+line)
                line=None
            else:
                out.append(line)
                print("another continued line:   "+line)
                line=None

            continue

        # This is not a continuation of a previous line
        if line is not None:
            if line.endswith(" _"):
                prevLineContinues=True
                print("remove ' _' from:   "+line)
                line=line[:-2]
            if inTable and line.startswith("||"):  # Another row of an existing table
                table.append(line)
                print("another row:   "+line)
                line=""
            elif inTable and not line.startswith("||"):    # The end of an existing table
                inTable=False
                # Process Table
                print("the table ends:   "+line)
                out.extend(ProcessTable(table))
                table=[]
                out.append(line)
            elif not inTable and line.startswith("||"):    # The start of a new table
                inTable=True
                table.append(line)
                print("a new table:   "+line)
                line=""
            elif not inTable and not line.startswith("||"):    # Just another non-table line
                out.append(line)
                print("another non-row:   "+line)
                line=""

    if len(table) > 0:
        out.extend(ProcessTable(table))
        print("add a left-over table")
    if line is not None and len(line) > 0:
        out.append(line)
        print("add the line:    "+line)
    return out


#=============================================================
# Check for Fancy table: Is this table a quote from Fancy 1 or Fancy 2?
# If 'yes' return "fancy1" or "fancy2".  If 'no', return None
def CheckForFancyTable(table):
    if table is None or len(table) == 0:
        return None

    # The Fancy table designation is always in the first line
    # The line is something like "|| from [[[Fancyclopedia 1]]]  ca. 1944 ||"
    # We'll look for just "from [[[Fancyclopedia 1" at the beginning of the text.  We'll allow for case variations, with or without the "[[[", and both 1 and 2
    # TODO: Need to add in support for supplement

    # First, remove any "||" as we know it's a table line and remove "[[[" is they're redundant for IDing.
    line=table[0].replace("||", "").replace("[[[", "")

    pattern="(.*)\s*[Ff]rom\s*Fancyclopedia\s*([12])"
    m=RegEx.search(pattern, line)
    if m is None:
        return None, None
    if len(m.groups()) != 2:
        return None, None

    if m.groups()[1] == "1":
        return "fancy1", m.groups()[0]
    return "fancy2", m.groups()[0]


#=============================================================
# Convert Wikidot's column spanning codes to SimpleTable's
def ConvertColspans(line):
    line=line.replace("||||||||||||||||~", '||~ colspan="8"|')
    line=line.replace("||||||||||||||||", '|| colspan="8"|')
    line=line.replace("||||||||||||||~", '||~ colspan="7"|')
    line=line.replace("||||||||||||||", '|| colspan="7"|')
    line=line.replace("||||||||||||~", '||~ colspan="6"|')
    line=line.replace("||||||||||||", '|| colspan="6"|')
    line=line.replace("||||||||||~", '||~ colspan="5"|')
    line=line.replace("||||||||||", '|| colspan="5"|')
    line=line.replace("||||||||~", '||~ colspan="4"|')
    line=line.replace("||||||||", '|| colspan="4"|')
    line=line.replace("||||||~", '||~ colspan="3"|')
    line=line.replace("||||||", '|| colspan="3"|')
    line=line.replace("||||~", '||~ colspan="2"|')
    line=line.replace("||||", '|| colspan="2"|')
    return line


#=============================================================
# Given a complete line in a table, split it into individual cells.
def AnalyzeTableLine(line):
    line=ConvertColspans(line)
    if "||~" in line:
        # The header line delimiters can be either "||" or "||~"
        line=line.replace("||~", "||")
    if "||" in line:
        cells=line.split("||")
    else:
        # Log an error?
        cells=[line]
        pass

    # We get empty list items due to the leading and trailing table "||"s.  Delete them.
    if len(cells) > 1 and cells[0].strip() == "":
        cells=cells[1:]
    if len(cells) > 1 and cells[-1].strip() == "":
        cells=cells[:-1]
    return cells


#=============================================================
# Given a list of cells, generate a MediaWiki SimpleTable line
def GenerateNewTableLine(line):
    newline=""
    for cell in line:
        newline+=cell+"||"
    newline=newline[:-2]  # We drop the last "||"
    return newline


#=============================================================
# Process a single table
# There are three kinds of tables:
#   Tables with merged cells
#   Fancy1 and Facy 2 quotes
#   Ordinary tables (no merged cells, no "Fancyclopedia 1" or "Fancyclopedia 1" in the first line).  Ordinary tables may or may not have a header row
def ProcessTable(table):

    # First, check to make sure there are no runs of more than two "|" -- that would indicate a table that can't be handled by
    # the SimpleTable thingie.
    # if CheckForAdvancedTable(table):
    #     print("this is an advanced table")
    #     return table

    out=[]
    # The second case is a Fancy 1 or Fancy 2 quote table
    fancy, prefix=CheckForFancyTable(table)
    if fancy is not None:
        out.append("{{"+fancy+"|text=")
        if prefix is not None and prefix.strip() is not "":
            out.append(prefix)
        for line in table[1:]:      # We skip the 1st line
            out.append(GenerateNewTableLine(AnalyzeTableLine(line)))
        out.append("}}")
    else:
        # Generate the output table's first line.
        # If the input table contains "||~" it's a headerline and will need some special handing in the output.
        header=AnalyzeTableLine(table[0])
        headerline="<tab class=wikitable sep=barbar "
        if "||~" in table[0]:
            headerline+="head=top "
        else:
            headerline+="head= "
        headerline+="border=1>\n"

        if "||~" in table[0]:
            if header is not None:
                for head in header:
                    headerline+=head+"||"
                headerline=headerline[:-2]    # We drop the last "||"
                table=table[1:]     # If we consume the header line here, remove it.
        out.append(headerline)

        # Now process the rest of the lines
        for line in table:
            out.append(GenerateNewTableLine(AnalyzeTableLine(line)))
        out.append("</tab>")

    return out


newSite=""
oldSite="../site/"
# page="alpha.txt"
# page="1967.txt"
# page="fanzine.txt"
# page="a.txt"
# page="1983-duff-results.txt"
# page="boskone.txt"
# page="individ-fanzine.txt"
# page="joe-fann.txt"
# page="apa.txt"
# page="scintillation.txt"
# page="1983-duff-results.txt"
# page="nova-award.txt"
# page="interlineations.txt"
page="alpha.txt"
newfile=ProcessFile(os.path.join(oldSite, page))
with open(os.path.join(newSite, page), "w") as file:
    newfile=[n+"\n" for n in newfile]
    file.writelines(newfile)