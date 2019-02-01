import os


#=============================================================
# Process a single table
def ProcessTable(lines):
    # < tab class =wikitable sep=bar head=top border=1 > Issue|Date|Pages|Notes|FAPA mailing
    # 1|1979|||134
    # 2|Undated|||Not in FAPA
    # </tab >

    # Analyze the table's first line.
    # If it contains "||~" it's a headerline and will need some special handing in the output.
    header=AnalyzeTableLine(lines[0])
    headerline="<tab class=wikitable sep=bar "
    if "||~" in lines[0]:
        headerline+="head=top "
    headerline+="border=1>"

    if "||~" in lines[0]:
        if header is not None:
            for head in header:
                headerline+=head+"|"
                headerline=headerline[:-1]    # We drop the last "|"
            lines=lines[1:]     # If we consume the header line here, remove it.
    out=[headerline]

    # Now process the rest of the lines
    for line in lines:
        out.append(GenerateNewTableLine(AnalyzeTableLine(line)))
    out.append("</tab>")
    return out


def AnalyzeTableLine(line):
    if "||~" in line:
        line=line.split("||~")
        line=[h.strip() for h in line]
    elif "||" in line:
        line=line.split("||")
        line=[h.strip() for h in line]
    else:
        # Log an error
        pass

    # We get empty list items due to the leading and trailing table "||"s.  Delete them.
    if line[0] == "":
        line=line[1:]
    if line[-1] == "":
        line=line[:-1]
    return line


def GenerateNewTableLine(line):
    newline=""
    for cell in line:
        newline+=cell+"|"
    newline=newline[:-1]  # We drop the last "|"
    return newline


#=============================================================
# Load a file, look for tables, if any are found, change them to SimpleTable format and write the result out
def ProcessFile(filename, newSite):
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
        line=line[:-1]  # Drop the "/n"

        # A line which follows a line ending with space-underscore will be handled the same way as the last line.  It can never begin or end a table.
        if prevLineContinues:
            if inTable:
                table.append(line)
                print("another continued row line:   "+line)
            else:
                out.append(line)
                print("another continued line:   "+line)

            prevLineContinues=line.endswith(" _")
            continue

        # This is not a continuation of a previous line
        if line.endswith(" _"):
            prevLineContinues=True
        if inTable and line.startswith("||"):  # Another row of an existing table
            table.append(line)
            print("another row:   "+line)
        elif inTable and not line.startswith("||"):    # The end of an existing table
            inTable=False
            # Process Table
            print("the table ends:   "+line)

            # Check to make sure there are no runs of more than two "|" -- that would indicate a table that can't be handled by
            # the SimpleTable thingie.
            if CheckForAdvancedTable(line, out, table):
                out.extend(table)  # Since we can't deal with the table as a table, just put it into the output.
                out.append(line)
                continue

            out.extend(ProcessTable(table))
            table=[]
            out.append(line)
        elif not inTable and line.startswith("||"):    # The start of a new table
            inTable=True
            table.append(line)
            print("a new table:   "+line)
        elif not inTable and not line.startswith("||"):    # Just another non-table line
            out.append(line)
            print("another non-row:   "+line)

    return out


def CheckForAdvancedTable(line, out, table):
    for tline in table:
        if "||||" in tline:
            # Log error message
            return True
    return False


newSite=""
page="1967.txt" #""apa.txt"
newfile=ProcessFile("../site/"+page, newSite)
with open(page, "w") as file:
    newfile=[n+"\n" for n in newfile]
    file.writelines(newfile)