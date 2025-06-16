from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count
from .models import Cliente, Projeto, Etapa, Material, Fornecedor, LancamentoFinanceiro,  DocumentoProjeto
from .forms import ProjetoForm, ClienteForm, EtapaForm, MaterialForm, FornecedorForm, LancamentoFinanceiroForm, DocumentoProjetoForm
from django.db.models import Sum
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.contrib.auth.hashers import check_password
import json


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

# Página inicial (Home)
@login_required
def home(request):
    return render(request, 'solar/home.html')

# Dashboard de Projetos
@login_required
def dashboard_projetos(request):
    projetos = Projeto.objects.all()
    total_projetos = projetos.count()
    em_andamento = projetos.filter(status="Em andamento").count()

    status_qs = projetos.values('status').annotate(total=Count('id'))
    status_labels = [s['status'] for s in status_qs]
    status_data = [s['total'] for s in status_qs]

    cliente_qs = projetos.values('cliente__nome').annotate(total=Count('id'))
    cliente_labels = [c['cliente__nome'] for c in cliente_qs]
    cliente_data = [c['total'] for c in cliente_qs]

    ultimos_projetos = projetos.order_by('-data_inicio')[:5]

    context = {
        'total_projetos': total_projetos,
        'em_andamento': em_andamento,
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'cliente_labels': json.dumps(cliente_labels),
        'cliente_data': json.dumps(cliente_data),
        'ultimos_projetos': ultimos_projetos,
    }
    return render(request, 'solar/dashboard_projetos.html', context)

@login_required
def upload_documento_projeto(request, projeto_id):
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    if request.method == 'POST':
        form = DocumentoProjetoForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.projeto = projeto
            doc.save()
            messages.success(request, 'Documento enviado com sucesso!')
            return redirect('detalhe_projeto', pk=projeto.id)
        else:
            messages.error(request, 'Erro ao enviar documento. Verifique os campos.')
    else:
        form = DocumentoProjetoForm()
    return render(request, 'solar/upload_documento_projeto.html', {'form': form, 'projeto': projeto})

@login_required
def excluir_documento_projeto(request, projeto_id, doc_id):
    projeto = get_object_or_404(Projeto, id=projeto_id)
    doc = get_object_or_404(DocumentoProjeto, id=doc_id, projeto=projeto)
    if request.method == 'POST':
        doc.arquivo.delete()  # Exclui o arquivo físico da pasta /media/
        doc.delete()          # Exclui o registro do banco
        messages.success(request, 'Documento excluído com sucesso!')
        return redirect('detalhe_projeto', pk=projeto.id)
    # Renderiza confirmação simples
    return render(request, 'solar/confirmar_exclusao_documento.html', {'documento': doc, 'projeto': projeto})

# Lista de clientes
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'solar/lista_clientes.html', {'clientes': clientes})

# Detalhes de cliente
@login_required
def detalhe_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'solar/detalhe_cliente.html', {'cliente': cliente})

# Lista de projetos
@login_required
def lista_projetos(request):
    projetos = Projeto.objects.all()
    return render(request, 'solar/lista_projetos.html', {'projetos': projetos})

# Detalhes de projeto
@login_required
def detalhe_projeto(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    return render(request, 'solar/detalhe_projeto.html', {'projeto': projeto})

# Cadastrar projeto
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

# Editar projeto
@login_required
def editar_projeto(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    if request.method == 'POST':
        form = ProjetoForm(request.POST, instance=projeto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Projeto atualizado com sucesso!')
            return redirect('detalhe_projeto', pk=projeto.pk)
        else:
            messages.error(request, 'Erro ao atualizar projeto. Verifique os campos.')
    else:
        form = ProjetoForm(instance=projeto)
    return render(request, 'solar/editar_projeto.html', {'form': form, 'projeto': projeto})

@login_required
def excluir_projeto(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    if request.method == 'POST':
        projeto.delete()
        messages.success(request, 'Projeto excluído com sucesso!')
        return redirect('lista_projetos')
    return render(request, 'solar/confirmar_exclusao_projeto.html', {'projeto': projeto})

# Cadastrar cliente
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

# Editar cliente
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

# Excluir cliente
@login_required
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.delete()
    messages.success(request, 'Cliente excluído com sucesso!')
    return redirect('lista_clientes')

# Cadastrar etapa (template provisório)
@login_required
def cadastrar_etapa(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)

    if request.method == 'POST':
        form = EtapaForm(request.POST)
        if form.is_valid():
            etapa = form.save(commit=False)
            etapa.projeto = projeto
            etapa.save()
            messages.success(request, 'Etapa cadastrada com sucesso!')
            return redirect('detalhe_projeto', pk=projeto.pk)
        else:
            messages.error(request, 'Erro ao cadastrar a etapa. Verifique os campos.')
    else:
        form = EtapaForm()

    return render(request, 'solar/cadastrar_etapa.html', {
        'form': form,
        'projeto': projeto
    })
# Lista de materiais
@login_required
def lista_materiais(request):
    materiais = Material.objects.all()
    return render(request, 'solar/lista_materiais.html', {'materiais': materiais})

# Cadastrar material
@login_required
def cadastrar_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material cadastrado com sucesso!')
            return redirect('lista_materiais')
        else:
            messages.error(request, 'Erro ao cadastrar material.')
    else:
        form = MaterialForm()
    return render(request, 'solar/cadastrar_material.html', {'form': form})

# Editar material
@login_required
def editar_material(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material atualizado com sucesso!')
            return redirect('lista_materiais')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'solar/editar_material.html', {'form': form, 'material': material})

# Lista de fornecedores
@login_required
def lista_fornecedores(request):
    fornecedores = Fornecedor.objects.all()
    return render(request, 'solar/lista_fornecedores.html', {'fornecedores': fornecedores})

# Cadastrar fornecedor
@login_required
def cadastrar_fornecedor(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor cadastrado com sucesso!')
            return redirect('lista_fornecedores')
        else:
            messages.error(request, 'Erro ao cadastrar fornecedor.')
    else:
        form = FornecedorForm()
    return render(request, 'solar/cadastrar_fornecedor.html', {'form': form})

# Editar fornecedor
@login_required
def editar_fornecedor(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor atualizado com sucesso!')
            return redirect('lista_fornecedores')
    else:
        form = FornecedorForm(instance=fornecedor)
    return render(request, 'solar/editar_fornecedor.html', {'form': form, 'fornecedor': fornecedor})


# Lista de lançamentos
@login_required
def lista_financeiro(request):
    lancamentos = LancamentoFinanceiro.objects.select_related('projeto').order_by('-data')
    return render(request, 'solar/lista_financeiro.html', {'lancamentos': lancamentos})

# Cadastrar lançamento
@login_required
def cadastrar_lancamento(request):
    if request.method == 'POST':
        form = LancamentoFinanceiroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lançamento registrado com sucesso!')
            return redirect('lista_financeiro')
        else:
            messages.error(request, 'Erro ao registrar lançamento.')
    else:
        form = LancamentoFinanceiroForm()
    return render(request, 'solar/cadastrar_lancamento.html', {'form': form})

@login_required
def dashboard_financeiro(request):
    projetos = Projeto.objects.all()
    lancamentos = LancamentoFinanceiro.objects.select_related('projeto')

    # Filtros
    projeto_id = request.GET.get('projeto')
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if projeto_id:
        lancamentos = lancamentos.filter(projeto_id=projeto_id)
    if tipo:
        lancamentos = lancamentos.filter(tipo=tipo)
    if status:
        lancamentos = lancamentos.filter(status=status)
    if data_inicio:
        lancamentos = lancamentos.filter(data__gte=parse_date(data_inicio))
    if data_fim:
        lancamentos = lancamentos.filter(data__lte=parse_date(data_fim))

    # Gráficos por tipo
    resumo_tipos = lancamentos.values('tipo').annotate(total=Sum('valor'))
    tipo_labels = [r['tipo'].capitalize() for r in resumo_tipos]
    tipo_data = [float(r['total']) for r in resumo_tipos]

    # Gráficos por projeto
    resumo_projetos = lancamentos.values('projeto__nome').annotate(total=Sum('valor')).order_by('-total')
    projeto_labels = [r['projeto__nome'] for r in resumo_projetos]
    projeto_data = [float(r['total']) for r in resumo_projetos]

    context = {
        'tipo_labels': json.dumps(tipo_labels),
        'tipo_data': json.dumps(tipo_data),
        'projeto_labels': json.dumps(projeto_labels),
        'projeto_data': json.dumps(projeto_data),
        'projetos': projetos,
        'filtro': {
            'projeto': projeto_id,
            'tipo': tipo,
            'status': status,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    }
    return render(request, 'solar/dashboard_financeiro.html', context)

# Login do cliente
def login_cliente(request):
    if request.method == 'POST':
        id_acesso = request.POST.get('id_acesso')
        senha = request.POST.get('senha')

        cliente = Cliente.objects.filter(id_acesso=id_acesso).first()
        if cliente and cliente.verificar_senha_acesso(senha):
            request.session['cliente_id'] = cliente.id
            return redirect('painel_cliente')
        else:
            messages.error(request, 'ID de acesso ou senha incorretos.')

    return render(request, 'solar/cliente_login.html')

# Logout do cliente
def logout_cliente(request):
    request.session.flush()
    return redirect('login_cliente')

# Painel do cliente
def painel_cliente(request):
    cliente_id = request.session.get('cliente_id')
    if not cliente_id:
        return redirect('login_cliente')

    cliente = get_object_or_404(Cliente, id=cliente_id)
    projetos = Projeto.objects.filter(cliente=cliente).order_by('-data_inicio')

    projetos_data = []
    for projeto in projetos:
        etapas = projeto.etapas.order_by('data_inicio')
        etapas_concluidas = etapas.exclude(data_fim__isnull=True).count()
        total_etapas = etapas.count()

        percentual = 0
        if total_etapas > 0:
            percentual = round((etapas_concluidas / total_etapas) * 100, 2)

        lancamentos = LancamentoFinanceiro.objects.filter(projeto=projeto)
        pagos = lancamentos.filter(status='pago').aggregate(total=Sum('valor'))['total'] or 0
        pendentes = lancamentos.filter(status='pendente').aggregate(total=Sum('valor'))['total'] or 0

        projetos_data.append({
            'projeto': projeto,
            'etapas': etapas,
            'etapas_concluidas': etapas_concluidas,
            'total_etapas': total_etapas,
            'percentual': percentual,
            'pagos': pagos,
            'pendentes': pendentes,
        })

    return render(request, 'solar/cliente_painel.html', {
        'cliente': cliente,
        'projetos_data': projetos_data
    })