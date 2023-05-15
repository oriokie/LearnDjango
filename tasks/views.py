from django.shortcuts import render
from django import forms
from django.urls import reverse
from django.http import HttpResponseRedirect
import openpyxl
from django.template import RequestContext
from django.http import HttpResponse
import pandas as pd
import sys
from .forms import FileForm, StatForm
from .models import File
from django.contrib import messages
from .models import Donor
from .changa import DonationForm
from django.shortcuts import render, redirect


pd.options.mode.chained_assignment = None  # default='warn'


class NewTaskForm(forms.Form):
    task = forms.CharField(label="New Task Name")
    priority = forms.IntegerField(label="Priority", min_value=1, max_value=4)


# Create your views here.
def index(request):
    if "tasks" not in request.session:
        request.session["tasks"] = []
    return render(request, "tasks/index.html", {"tasks": request.session["tasks"]})


def add(request):
    if request.method == "POST":
        form = NewTaskForm(request.POST)
        if form.is_valid():
            task = form.cleaned_data["task"]
            request.session["tasks"] += [task]
            return HttpResponseRedirect(reverse("tasks:index"))
        else:
            return render(request, "tasks/add.html", {"form": form})

    return render(request, "tasks/add.html", {"form": NewTaskForm()})


def upload_file(request):
    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # return redirect('file_list')
    else:
        form = FileForm()
    return render(request, "upload.html", {"form": form})


def read(request):
    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            # Get the uploaded file
            excel_fileSTAT = "media/STATEMENT"
            excel_fileEFT = "media/EFT.xls"
            excel_fileDD = "media/DD.xls"
            excel_fileCHQ = "media/KES.xls"

            sdf = pd.read_fwf(
                excel_fileSTAT, header=None, widths=[13, 20, 15, 9, 32, 16], index=False
            )

            sortdf = sdf.sort_values(0)

            val = sortdf.loc[(sortdf[1] == "BALANCE AT PERIOD EN"), 4].iloc[0]

            df = sortdf.loc[sortdf[5].isin(["KES1020000010001"])]
            df.loc[df[4].str.endswith("-"), 4] = "-" + df.loc[
                df[4].str.endswith("-"), 4
            ].str.strip("- ")
            pd.to_numeric([4])

            cleandf = df[[1, 2, 4]]
            cleandf.columns = ["NARRATION", "FT", "AMOUNT"]

            cleandf["AMOUNT"] = cleandf["AMOUNT"].str.replace(",", "").astype(float)

            cleandf = cleandf.sort_values(["AMOUNT"])

            print(cleandf.head(2))

            postivesum = cleandf[cleandf["AMOUNT"] > 0]["AMOUNT"].sum()
            negativesum = cleandf[cleandf["AMOUNT"] < 0]["AMOUNT"].sum()

            DDrawreport = pd.read_excel(excel_fileDD, index_col=False)
            DDrawreport[["PROCNO", "DESTACCOUNT"]] = DDrawreport[
                ["PROCNO", "DESTACCOUNT"]
            ].astype(str)
            DDreport = DDrawreport[
                (
                    DDrawreport["STATUSID"].isin([1])
                    & (
                        ~DDrawreport["DESTBANK"].isin(
                            ["NCBA BANK KENYA PLC", "NIC BANK PLC"]
                        )
                    )
                )
            ]
            DDdf = DDreport[["POLICY1", "FTREFERENCE", "AMOUNT"]]
            DDdf.columns = ["POLICY1", "FT", "AMOUNT"]
            DDdf["AMOUNT"] = DDdf["AMOUNT"].astype(float)

            DDsum = DDdf["AMOUNT"].sum()

            EFTdata = pd.read_excel(excel_fileEFT, index_col=False)
            EFTdata[["PROCNO", "DESTACCOUNT"]] = EFTdata[
                ["PROCNO", "DESTACCOUNT"]
            ].astype(str)
            EFTdf = EFTdata[["ACHBULKID", "TRNREF", "AMOUNT"]]
            EFTdf.columns = ["ACHBULKID", "FT", "AMOUNT"]
            # EFTdf ['AMOUNT'] = EFTdf ['AMOUNT'].astype(float)
            EFTsum = EFTdf["AMOUNT"].sum()

            CHQraw = pd.read_excel(excel_fileCHQ, index_col=False)
            CHQraw[["PROCNO", "DESTACCOUNT", "CHEQUENO"]] = CHQraw[
                ["PROCNO", "DESTACCOUNT", "CHEQUENO"]
            ].astype(str)

            if "STATUSID" in CHQraw:
                print("STATUSID FOUND")
                CHQs = CHQraw[
                    (
                        CHQraw["STATUSID"].isin([1])
                        & (
                            ~CHQraw["DESTBANK"].isin(
                                ["NCBA BANK KENYA PLC", "NIC BANK PLC"]
                            )
                        )
                        & (CHQraw["STAGE"].isin(["ACH CREATION", "COMPLETE"]))
                    )
                ]
            else:
                print("NO EXCLUDED CHEQUES FOUND")
                CHQs = CHQraw[
                    (~CHQraw["DESTBANK"].isin(["NCBA BANK KENYA PLC", "NIC BANK PLC"]))
                    & (CHQraw["STAGE"].isin(["ACH CREATION"]))
                ]

            if CHQs["CBS_REJECT_REASON"].str.contains("NOCREDIT").any():
                print("CREDIT-DUPLICATE VALUES")
                CHQdf = CHQs[["CHEQUENO", "CBS_REJECT_REASON", "AMOUNT"]]
                CHQdf[["FT", "FT1", "FT2"]] = CHQdf.CBS_REJECT_REASON.str.split(
                    "[,-]", expand=True
                )
                CHQclr = CHQdf[["CHEQUENO", "FT1", "AMOUNT"]]
                CHQclr.columns = ["CHEQUENO", "FT", "AMOUNT"]
            else:
                CHQdf = CHQs[["CHEQUENO", "CBS_REJECT_REASON", "AMOUNT"]]
                CHQdf[["FT", "FT1"]] = CHQdf.CBS_REJECT_REASON.str.split(
                    "[,]", expand=True
                )
                CHQclr = CHQdf[["CHEQUENO", "FT1", "AMOUNT"]]
                CHQclr.columns = ["CHEQUENO", "FT", "AMOUNT"]
                print("NO DUPLICATE ENTRIES")

            CHQsum = CHQclr["AMOUNT"].sum()

            print(CHQclr.head(2))

            print("Let Reconciliation Begin")

            frames = [DDdf, EFTdf, CHQclr]

            allcleared = pd.concat(frames)

            left_join = pd.merge(cleandf, allcleared, on="FT", how="left")

            T24E = left_join[(~left_join["AMOUNT_y"].notnull())]

            left_join2 = pd.merge(allcleared, cleandf, on="FT", how="left")

            CPE = left_join2[(~left_join2["AMOUNT_y"].notnull())]

            totaldebits = DDsum + CHQsum
            summarydata = [
                ["TOTAL STATEMENT CREDITS", postivesum],
                ["TOTAL STATEMENT DEBITS", negativesum],
                ["DIRECT DEBITS", DDsum],
                ["CHEQUES", CHQsum],
                ["EFTs", EFTsum],
                ["TOTAL DEBITS CLEARED", totaldebits],
                ["BALANCE AT THE END", val],
            ]
            summarydf = pd.DataFrame(summarydata, columns=["DESCRIPTION", "AMOUNT"])

            reversals = cleandf[cleandf.duplicated(["FT"], keep=False)]
            reversals2 = allcleared[
                (allcleared.duplicated(["FT"], keep=False))
                & (allcleared["FT"].str.contains("FT"))
            ]

            CHQsDf = CHQs.applymap(
                lambda x: x.encode(
                    "unicode_escape"
                ).decode(  # Basically, it escapes the unicode characters if they exist
                    "utf-8"
                )
                if isinstance(x, str)
                else x
            )

            amountcheck = left_join[(left_join["AMOUNT_y"].notnull())]
            amountcheck["Diff"] = amountcheck["AMOUNT_y"] - abs(amountcheck["AMOUNT_x"])

            WorryDiff = amountcheck.loc[(abs(amountcheck.Diff)) > 0.5]

            context = {"summarydata": summarydata}

            output_path = "./Recon.xlsx"
            with pd.ExcelWriter(output_path) as writer:
                cleandf.to_excel(writer, sheet_name="Statement", index=False)
                print("Copied the Statement Entries")
                allcleared.to_excel(writer, sheet_name="Cleared", index=False)
                print("Copied the CP Cleared Entries")
                T24E.to_excel(writer, sheet_name="T24 Exceptions", index=False)
                print("Created T24 Exceptions")
                CPE.to_excel(writer, sheet_name="CP Exceptions", index=False)
                print("Created Chequepoint Exceptions")
                summarydf.to_excel(writer, sheet_name="Summary", index=False)
                print("Created the Summary Sheet")
                DDreport.to_excel(writer, sheet_name="DDS", index=False)
                print("Copied Cleared DDs")
                EFTdata.to_excel(writer, sheet_name="EFTs", index=False)
                print("Copied Cleared EFTs")
                CHQsDf.to_excel(writer, sheet_name="CHQs", index=False)
                print("Copied Cleared CHQs")
                reversals.to_excel(
                    writer, sheet_name="REVERSALS FROM LIVE", index=False
                )
                print("Reversals Detected...")
                WorryDiff.to_excel(writer, sheet_name="AMOUNT_CHECK", index=False)
                reversals2.to_excel(writer, sheet_name="CLEARED DUPLICATE", index=False)

            html = render(request, "tasks/read.html", context)
            response = HttpResponse(content_type="text/html")
            response.write(html)

            # Add the binary file to the response
            with open("Recon.xlsx", "rb") as f:
                response.content = f.read()
                response["Content-Disposition"] = 'attachment; filename="Recon.xlsx"'

                return response

    else:
        form = FileForm()

    return render(request, "tasks/read.html", {"form": form, "process_complete": False})


def donate(request):
    if request.method == "POST":
        form = DonationForm(request.POST)
        if form.is_valid():
            donor = Donor(
                name=form.cleaned_data["name"], donation=form.cleaned_data["donation"]
            )
            donor.save()
            return redirect("tasks/donors_list.html")

    else:
        form = DonationForm()
    return render(request, "tasks/donate.html", {"form": form})


def donors_list(request):
    donors = Donor.objects.all()
    return render(request, "tasks/donors_list.html", {"donors": donors})


def stat(request):
    if request.method == "POST":
        form = StatForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            # Get the uploaded file
            excel_fileSTAT = "media/STATEMENT"

            sdf = pd.read_fwf(
                excel_fileSTAT, header=None, widths=[13, 20, 15, 9, 32, 16], index=False
            )

            sortdf = sdf.sort_values(0)

            val = sortdf.loc[(sortdf[1] == "BALANCE AT PERIOD EN"), 4].iloc[0]

            df = sortdf.loc[sortdf[5].isin(["KES1020000010001"])]
            df.loc[df[4].str.endswith("-"), 4] = "-" + df.loc[
                df[4].str.endswith("-"), 4
            ].str.strip("- ")
            pd.to_numeric([4])

            cleandf = df[[1, 2, 4]]
            cleandf.columns = ["NARRATION", "FT", "AMOUNT"]

            cleandf["AMOUNT"] = cleandf["AMOUNT"].str.replace(",", "").astype(float)

            cleandf = cleandf.sort_values(["AMOUNT"])

            print(cleandf.head(2))

            output_path = "./Statement.xlsx"

            with pd.ExcelWriter(output_path) as writer:
                cleandf.to_excel(writer, sheet_name="Statement", index=False)

            html = render(request, "tasks/stat.html")
            response = HttpResponse(content_type="text/html")
            response.write(html)

            # Add the binary file to the response
            with open("Statement.xlsx", "rb") as f:
                response.content = f.read()
                response[
                    "Content-Disposition"
                ] = 'attachment; filename="Statement.xlsx"'

                return response

    else:
        form = StatForm()

    return render(request, "tasks/stat.html", {"form": form, "process_complete": False})
