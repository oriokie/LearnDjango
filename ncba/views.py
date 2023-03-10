from django.shortcuts import render, redirect
from .forms import FileForm
from .models import File

def upload_file(request):
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('file_list')
    else:
        form = FileForm()
    return render(request, 'upload.html', {'form': form})

def file_list(request):
    files = File.objects.all()
    return render(request, 'file_list.html', {'files': files})
