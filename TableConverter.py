import os



#=============================================================
# Load a file, look for tables, if any are found, change them to SimpleTable format and return the result
def ProcessFile(filename):
    if not os.path.exists(filename):
        #log.Write()
        return

    # Read the file
    with open(filename) as file:
        source=file.readlines()

    # A table starts with a line that begins "||"
    # It continues until there's a line that does *not* begin with "||"
    # (Remember that lines can be continued by ending them with " _")
    out=[]
    table=[]
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
            else:
                out.append(line)
                print("another continued line:   "+line)

            continue

        # This is not a continuation of a previous line
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

            # Check to make sure there are no runs of more than two "|" -- that would indicate a table that can't be handled by
            # the SimpleTable thingie.
            if CheckForAdvancedTable(table):
                out.extend(table)  # Since we can't deal with the table as a table, just put it into the output.
                table=[]
                out.append(line)
                line=""
                print("this is an advanced table")
                continue

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
        # Check to make sure there are no runs of more than two "|" -- that would indicate a table that can't be handled by
        # the SimpleTable thingie.
        if CheckForAdvancedTable(table):
            out.extend(table)  # Since we can't deal with the table as a table, just put it into the output.
            table=[]
            out.append(line)
            line=""
            print("this is an advanced table")

        if len(table) > 0:
            out.extend(ProcessTable(table))
            print("add a left-over table and a line::   "+line)
            table=[]
        if len(line) > 0:
            out.append(line)
            line=""
    return out


#=============================================================
# Look for advanced table features (like merged cells) which the MediaWiki SimpleTable can't handle.
def CheckForAdvancedTable(table):
    for tline in table:
        if "||||" in tline:
            # Log error message
            return True
    return False


#=============================================================
# Process a single table
def ProcessTable(lines):
    # < tab class =wikitable sep=bar head=[top] border=1 > Issue|Date|Pages|Notes|FAPA mailing
    # 1|1979|||134
    # 2|Undated|||Not in FAPA
    # </tab >

    # Generate the output table's first line.
    # If the input table contains "||~" it's a headerline and will need some special handing in the output.
    header=AnalyzeTableLine(lines[0])
    headerline="<tab class=wikitable sep=bar "
    if "||~" in lines[0]:
        headerline+="head=top "
    else:
        headerline+="head= "
    headerline+="border=1>"

    out=[]
    if "||~" in lines[0]:
        if header is not None:
            for head in header:
                headerline+=head+"|"
                headerline=headerline[:-1]    # We drop the last "|"
            lines=lines[1:]     # If we consume the header line here, remove it.
    out.append(headerline)

    # Now process the rest of the lines
    for line in lines:
        out.append(GenerateNewTableLine(AnalyzeTableLine(line)))
    out.append("</tab>")
    return out


#=============================================================
# Given a complete line in a table, split it into individual cells.
def AnalyzeTableLine(line):
    if "||~" in line:
        cells=line.split("||~")
        cells=[h.strip() for h in cells]
    elif "||" in line:
        cells=line.split("||")
        cells=[h.strip() for h in cells]
    else:
        # Log an error?
        cells=[line]
        pass

    # We get empty list items due to the leading and trailing table "||"s.  Delete them.
    if len(cells) > 1 and cells[0] == "":
        cells=cells[1:]
    if len(cells) > 1 and cells[-1] == "":
        cells=cells[:-1]
    return cells


#=============================================================
# Given a list of cells, generate a MediaWiki SimpleTable line
def GenerateNewTableLine(line):
    newline=""
    for cell in line:
        newline+=cell+"|"
    newline=newline[:-1]  # We drop the last "|"
    return newline




newSite=""
oldSite="../site/"
page="1967.txt"
page="apa.txt"
page="fanzine.txt"
page="boskone.txt"
newfile=ProcessFile(os.path.join(oldSite, page))
with open(os.path.join(newSite, page), "w") as file:
    newfile=[n+"\n" for n in newfile]
    file.writelines(newfile)