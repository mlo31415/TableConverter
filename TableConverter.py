import os


#=============================================================
# Process a single table
def ProcessTable(lines):
    # < tab class =wikitable sep=bar head=top border=1 > Issue|Date|Pages|Notes|FAPA mailing
    # 1|1979|||134
    # 2|Undated|||Not in FAPA
    # </tab >

    newline="<tab class =wikitable sep=bar head=top border=1> "
    # The first line of a table is the header.  It's delimited by either "||" or "||~"
    header=lines[0]
    if "||~" in header:
        header=header.split("||~")
        header=[h.strip() for h in header]
    elif "||" in header:
        header=header.split("||")
        header=[h.strip() for h in header]
    else:
        # Log an error
        pass

    for head in header:
        newline+=head+"|"
    newline=newline[:-1]    # We drop the last "|"
    out=[newline]

    # Now process the rest of the lines
    lines=lines[1:]
    for line in lines:
        newline=""
        if "||~" in line:
            line=line.split("||~")
            line=[h.strip() for h in line]
        elif "||" in line:
            line=line.split("||")
            line=[h.strip() for h in line]
        else:
            # Log an error
            pass
        for cell in line:
            newline+=cell+"|"
        newline=newline[:-1]    # We drop the last "|"
        out.append(newline)
    return out

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
            for tline in table:
                if "||||" in tline:
                    # Log error message
                    out.extend(table)   # Since we can't deal with the table as a table, just put it into the output.
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



newSite=""
ProcessFile("../site/apa.txt", newSite)