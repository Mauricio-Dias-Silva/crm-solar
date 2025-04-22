from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Cliente, Projeto
from .forms import ProjetoForm, ClienteForm

def home(request):
    return render(request, 'solar/home.html')

def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'solar/lista_clientes.html', {'clientes': clientes})

def detalhe_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'solar/detalhe_cliente.html', {'cliente': cliente})

def lista_projetos(request):
    projetos = Projeto.objects.all()
    return render(request, 'solar/lista_projetos.html', {'projetos': projetos})

def detalhe_projeto(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    return render(request, 'solar/detalhe_projeto.html', {'projeto': projeto})

def cadastrar_projeto(request):
    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Projeto cadastrado com sucesso!')
            return redirect('lista_projetos')
        else:
            messages.error(request, 'Erro ao cadastrar projeto. Verifique os campos.')
    else:
        form = ProjetoForm()
    return render(request, 'solar/cadastrar_projeto.html', {'form': form})

def cadastrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente cadastrado com sucesso!')
            return redirect('lista_clientes')
        else:
            messages.error(request, 'Erro ao cadastrar cliente. Verifique os campos.')
    else:
        form = ClienteForm()
    return render(request, 'solar/cadastrar_cliente.html', {'form': form})

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('detalhe_cliente', pk=cliente.pk)
        else:
            messages.error(request, 'Erro ao atualizar cliente. Verifique os campos.')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'solar/editar_cliente.html', {'form': form, 'cliente': cliente})

# Função de excluir cliente
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.delete()  # Exclui o cliente
    messages.success(request, 'Cliente excluído com sucesso!')
    return redirect('lista_clientes')  # Redireciona para a lista de clientes

def cadastrar_etapa(request, pk):
    # Aqui você pode adicionar lógica específica da etapa
    return render(request, 'template.html')
