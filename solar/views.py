from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .models import Cliente, Projeto
from .forms import ProjetoForm, ClienteForm

# Tela inicial de login
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Redireciona para a página inicial após login
        else:
            messages.error(request, 'Credenciais inválidas')
    else:
        form = AuthenticationForm()
    return render(request, 'solar/login.html', {'form': form})

# Página inicial (Home) - Protegida por login_required
@login_required
def home(request):
    return render(request, 'solar/home.html')

# Lista de clientes - Protegida por login_required
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'solar/lista_clientes.html', {'clientes': clientes})

# Detalhes de um cliente - Protegida por login_required
@login_required
def detalhe_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'solar/detalhe_cliente.html', {'cliente': cliente})

# Lista de projetos - Protegida por login_required
@login_required
def lista_projetos(request):
    projetos = Projeto.objects.all()
    return render(request, 'solar/lista_projetos.html', {'projetos': projetos})

# Detalhes de um projeto - Protegida por login_required
@login_required
def detalhe_projeto(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    return render(request, 'solar/detalhe_projeto.html', {'projeto': projeto})

# Cadastrar projeto - Protegida por login_required
@login_required
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

# Cadastrar cliente - Protegida por login_required
@login_required
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

# Editar cliente - Protegida por login_required
@login_required
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

# Função de excluir cliente - Protegida por login_required
@login_required
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.delete()  # Exclui o cliente
    messages.success(request, 'Cliente excluído com sucesso!')
    return redirect('lista_clientes')  # Redireciona para a lista de clientes

# Função de cadastrar etapa - (ainda a ser definida conforme sua lógica)
@login_required
def cadastrar_etapa(request, pk):
    # Aqui você pode adicionar lógica específica da etapa
    return render(request, 'template.html')
