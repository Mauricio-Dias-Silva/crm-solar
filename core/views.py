import os
import shutil
import tempfile
# Para a publicação Docker, estes imports serão necessários DENTRO da publish_site_view.
# import docker 

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils.text import slugify
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages 
import google.api_core.exceptions # Para capturar erros específicos do Gemini
import uuid # Para nomes de arquivo únicos no upload de imagens
from django.core.files.storage import default_storage # Para upload de arquivos
from django.core.files.base import ContentFile # Para upload de arquivos


# Importe suas funções utilitárias APENAS AQUI.
from .models import SiteProject
from .utils import extract_placeholders, inject_content_into_html, add_editable_attributes 


# --- AI CLIENT INITIALIZATION HELPER FUNCTION (Chamada dentro das views) ---
def get_ai_client(provider):
    # Imports são feitos localmente para garantir que o StatReloader do Django os recarregue corretamente.
    if provider == "gemini":
        try:
            import google.generativeai as genai_module 
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not found in settings.")
            genai_module.configure(api_key=settings.GEMINI_API_KEY)
            return genai_module.GenerativeModel('models/gemini-1.5-flash'), genai_module # Retorna modelo e módulo
        except Exception as e:
            raise Exception(f"Falha ao inicializar modelo Gemini: {e}")
    elif provider == "openai":
        try:
            import openai as openai_module 
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found in settings.")
            return openai_module.OpenAI(api_key=settings.OPENAI_API_KEY), openai_module # Retorna cliente e módulo
        except Exception as e:
            raise Exception(f"Falha ao inicializar cliente OpenAI: {e}")
    else:
        raise ValueError(f"Provedor de IA desconhecido: {provider}")


# --- VIEWS PRINCIPAIS ---

def home_view(request):
    return render(request, 'core/home.html')


@login_required
def create_site_view(request):
    generated_code = None
    user_prompt_input = "" 
    error_message = None

    selected_ai_provider = settings.DEFAULT_AI_PROVIDER 

    # Extrai dados do cliente GET para pré-preencher o prompt (se houver)
    cliente_id_from_url = request.GET.get('cliente_id')
    cliente_nome_from_url = request.GET.get('cliente_nome')
    prompt_inicial_from_url = request.GET.get('prompt_inicial')

    # Lógica para requisições GET (primeiro acesso à página)
    if request.method == 'GET':
        if prompt_inicial_from_url:
            user_prompt_input = prompt_inicial_from_url
        
        return render(request, 'core/create_site.html', {
            'user_prompt': user_prompt_input, 
            'cliente_id': cliente_id_from_url,
            'cliente_nome': cliente_nome_from_url,
            'prompt_inicial': prompt_inicial_from_url
        })
    
    # Lógica para requisições POST (usuário clicou em 'Gerar Código')
    elif request.method == 'POST':
        user_prompt_input = request.POST.get('prompt', '') 
        
        # Prepara a instância do cliente (apenas se vier de POST e não já definida por GET)
        cliente_instance = None
        cliente_id_from_post = request.POST.get('cliente_id')
        if cliente_id_from_post: 
             try:
                # Importa Cliente localmente para evitar importações circulares e problemas de carregamento
                from solar.models import Cliente 
                cliente_instance = Cliente.objects.get(id=cliente_id_from_post)
             except Cliente.DoesNotExist:
                messages.warning(request, "Cliente associado não encontrado. O site será gerado sem vínculo.")


        if not user_prompt_input: # Se o prompt estiver vazio
            error_message = "Por favor, forneça uma descrição para o site."
            messages.error(request, error_message)
            return render(request, 'core/create_site.html', {
                'generated_code': generated_code,
                'user_prompt': user_prompt_input,
                'error_message': error_message,
                'cliente_id': request.POST.get('cliente_id'), 
                'cliente_nome': request.POST.get('cliente_nome'),
                'prompt_inicial': request.POST.get('prompt_inicial')
            })
        
        # --- INÍCIO DO BLOCO DE GERAÇÃO DA IA ---
        try:
            print(f"DEBUG: Tentando gerar conteúdo usando {selected_ai_provider} com prompt: {user_prompt_input[:50]}...")
            
            ai_client, ai_module = get_ai_client(selected_ai_provider) 
            
            ai_system_prompt = (
                "Você é um designer de landing pages estáticas e desenvolvedor front-end experiente, altamente qualificado em HTML5, CSS3 (com foco em classes Bootstrap 5 para responsividade) e JavaScript minimalista. "
                "Sua missão é criar landing pages visualmente deslumbrantes, intuitivas e altamente responsivas para diversos nichos. "
                "Siga rigorosamente os princípios de UI/UX modernos: priorize a hierarquia visual clara, espaçamento (padding e margin) adequado para legibilidade, paletas de cores harmoniosas (complementares e/ou análogas), tipografia limpa e legível (evitando excesso de fontes), e transições suaves para uma experiência fluida."
                "Design Responsivo: Garanta que o layout seja impecável em todos os dispositivos (desktop, tablet, mobile) utilizando as classes de grid e utilitários de responsividade do Bootstrap 5."
                "Criatividade Visual: Não se limite a layouts genéricos. Pense em como criar seções visualmente interessantes, com fundos que se complementam, uso sutil de sombras, bordas arredondadas e efeitos de hover para botões e links (apenas CSS). Incorpore um estilo que transmita a essência da descrição do usuário."
                "Estrutura do Código: O código deve ser semântico (usando `<header>`, `<main>`, `<section>`, `<footer>`, etc.), bem comentado e fácil de entender. Inclua o CSS em um bloco `<style>` no `<head>` (para estilos específicos da página) e referencie o Bootstrap via CDN."
                
                "Use os seguintes placeholders EXATOS para o conteúdo editável pelo usuário. Insira esses placeholders diretamente no HTML:"
                "`[LP_HERO_TITULO]`, `[LP_HERO_SUBTITULO]`, `[LP_HERO_CTA_TEXTO]`, `[LP_HERO_CTA_LINK]`, "
                "`[LP_BENEFICIO_1_TITULO]`, `[LP_BENEFICIO_1_DESCRICAO]`, `[LP_BENEFICIO_2_TITULO]`, `[LP_BENEFICIO_2_DESCRICAO]`, `[LP_BENEFICIO_3_TITULO]`, `[LP_BENEFICIO_3_DESCRICAO]`, "
                "`[DEP_1_TEXTO]`, `[DEP_1_NOME]`, `[DEP_2_TEXTO]`, `[DEP_2_NOME]`, `[DEP_3_TEXTO]`, `[DEP_3_NOME]`, "
                "`[FORM_TITULO]`, `[FORM_SUBMIT_TEXTO]`, "
                "`[LP_RODAPE_COPYRIGHT]`, `[LP_LINK_FACEBOOK]`, `[LP_LINK_INSTAGRAM]`. "
                "Para imagens de conteúdo (como em galerias, perfis, ou dentro de seções de benefício/característica), gere a tag `<img>` com um placeholder `src` da seguinte forma: "
                "`<img src=\"[LP_IMAGEM_SECAO_NOME_URL]\" alt=\"[LP_IMAGEM_SECAO_NOME_ALT]\" class=\"img-fluid\">`. "
                "Substitua 'SECAO_NOME' e 'NOME' por algo descritivo como 'GALERIA_1', 'BENEFICIO_1', 'DEP_1_FOTO'. "
                "Se houver uma imagem de fundo na seção hero, use `background-image: url('[LP_HERO_BG_IMAGEM_URL]');` diretamente no CSS. "
                "Gere no mínimo 3 placeholders de imagem de conteúdo e 1 para imagem de fundo na Hero Section, se aplicável ao contexto. "
                
                "NÃO inclua PHP, Python de backend, ou qualquer script de servidor. O JavaScript deve ser mínimo, apenas para funcionalidades de front-end (ex: Bootstrap carrosséis, efeitos de scroll, formulário simples de contato que pode ser configurado via Formspree ou similar se houver um placeholder para URL de action)."
                "Retorne APENAS o código HTML completo, sem qualquer texto introdutório, explicações ou markdown extra como ```html."
            )

            ai_user_prompt = (
                f"Gere uma landing page com base na seguinte descrição: '{user_prompt_input}'. "
                "A página deve ser visualmente atraente e seguir as últimas tendências de design. "
                "Inclua as seções: Hero, 3 Benefícios, 3 Depoimentos, Formulário de Contato e Rodapé. "
                "O design deve ser moderno e clean, com um uso inteligente de cores e espaçamento para melhorar a legibilidade e a estética. "
                "Pense em um esquema de cores profissional e uma tipografia agradável. "
                "Se a descrição implicar em um estilo visual específico, incorpore-o. "
                "Mantenha-o genérico para os placeholders de TEXTO e use os placeholders de IMAGEM conforme as instruções do sistema."
            )

            if selected_ai_provider == "gemini":
                response = ai_client.generate_content(
                    [ai_system_prompt, ai_user_prompt],
                    generation_config=ai_module.GenerationConfig(
                        temperature=0.3, 
                        max_output_tokens=2000
                    ),
                    request_options={'timeout': 120} 
                )
                generated_code = response.text
            elif selected_ai_provider == "openai":
                response = ai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": ai_system_prompt},
                        {"role": "user", "content": ai_user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    timeout=120
                )
                generated_code = response.choices[0].message.content
            else: 
                error_message = "Erro: Provedor de IA não configurado ou chave de API ausente/inválida. Verifique settings.py"
                messages.error(request, error_message)
                print(error_message)
                generated_code = ""
            
            print(f"DEBUG: Resposta da IA recebida. Tamanho: {len(generated_code) if generated_code else 0}")

            if generated_code and generated_code.strip().startswith("```") and generated_code.strip().endswith("```"):
                generated_code = generated_code.replace("```html\n", "").replace("```\n", "").strip()
                generated_code = generated_code.replace("```html", "").replace("```", "").strip()

            print(f"DEBUG: Após remover markdown. Tamanho: {len(generated_code.strip()) if generated_code else 0}")
            
            if generated_code and len(generated_code.strip()) > 100 and "<html" in generated_code.lower() and "<head" in generated_code.lower() and "<body" in generated_code.lower():
                print(f"\n--- DEBUG: Código HTML final para exibição (início):")
                print(generated_code[:500])
                print("--- FIM DEBUG ---\n")
                
                # --- AQUI VAI SALVAR O PROJETO E REDIRECIONAR ---
                # A função add_editable_attributes é essencial para o fluxo de edição posterior.
                # Não a removeremos para esta versão final, mas ela precisa estar em utils.py
                processed_html_code = add_editable_attributes(generated_code) 

                initial_project_name = f"LP - {user_prompt_input[:70]}{'...' if len(user_prompt_input) > 70 else ''}"
                
                project = SiteProject.objects.create(
                    user=request.user,
                    cliente_associado=cliente_instance, # 'cliente_instance' pode ser None, o que é OK
                    original_prompt=user_prompt_input,
                    base_html_code=processed_html_code, # Salva o HTML com os atributos editáveis
                    name=initial_project_name,
                    content_data={} # Inicializa com dicionário vazio
                )
                messages.success(request, f"Site '{initial_project_name}' gerado com sucesso! Agora personalize o conteúdo.")
                print(f"Projeto {project.id} salvo! Redirecionando para edição...")
                return redirect('core:edit_site', project_id=project.id)
                # --- FIM DA ATIVAÇÃO ---
            else:
                error_message = "O código gerado pela IA é inválido ou muito curto. Por favor, tente um prompt diferente ou ajuste os parâmetros da IA."
                messages.error(request, error_message)
                print(f"Código IA inválido ou muito curto. Tamanho: {len(generated_code.strip()) if generated_code else 0}")
                print(f"Código Gerado (amostra): {generated_code[:200] if generated_code else 'None'}")
                # A execução cairá para o render final da view, exibindo o erro.

        except google.api_core.exceptions.GoogleAPIError as e: 
            error_message = f"Erro da API Gemini: {e}. Status: {getattr(e, 'response', None)}. Verifique a chave API, permissões ou limites de taxa."
            messages.error(request, error_message)
            print(f"!!! ERRO DA API GEMINI: {e} !!!")
        except Exception as e: 
            error_message = f"Erro durante a Geração/Pós-processamento da IA ({selected_ai_provider}): {e}. Por favor, verifique os logs do servidor."
            messages.error(request, error_message)
            print(f"!!! ERRO FATAL NA GERAÇÃO/PÓS-PROCESSAMENTO ({selected_ai_provider}): {e}")
            
    # Este é o retorno final para POST requests que não resultaram em redirecionamento.
    return render(request, 'core/create_site.html', {
        'generated_code': generated_code,
        'user_prompt': user_prompt_input,
        'error_message': error_message,
        'cliente_id': request.POST.get('cliente_id'),
        'cliente_nome': request.POST.get('cliente_nome'),
        'prompt_inicial': request.POST.get('prompt_inicial')
    })


@login_required
def edit_site_view(request, project_id):
    project = get_object_or_404(SiteProject, id=project_id, user=request.user)
    placeholders = extract_placeholders(project.base_html_code) 

    image_fields_map = {
        'lp_hero_bg_imagem_url_file': ('LP_HERO_BG_IMAGEM_URL', None), 
        'lp_imagem_secao_galeria_1_url_file': ('LP_IMAGEM_SECAO_GALERIA_1_URL', 'LP_IMAGEM_SECAO_GALERIA_1_ALT'),
        'lp_imagem_secao_galeria_2_url_file': ('LP_IMAGEM_SECAO_GALERIA_2_URL', 'LP_IMAGEM_SECAO_GALERIA_2_ALT'),
        'lp_imagem_secao_galeria_3_url_file': ('LP_IMAGEM_SECAO_GALERIA_3_URL', 'LP_IMAGEM_SECAO_GALERIA_3_ALT'),
        'lp_imagem_beneficio_1_url_file': ('LP_IMAGEM_BENEFICIO_1_URL', 'LP_IMAGEM_BENEFICIO_1_ALT'), 
        'lp_imagem_beneficio_2_url_file': ('LP_IMAGEM_BENEFICIO_2_URL', 'LP_IMAGEM_BENEFICIO_2_ALT'), 
        'lp_imagem_beneficio_3_url_file': ('LP_IMAGEM_BENEFICIO_3_URL', 'LP_IMAGEM_BENEFICIO_3_ALT'), 
        'lp_imagem_dep_1_photo_url_file': ('LP_IMAGEM_DEP_1_PHOTO_URL', 'LP_IMAGEM_DEP_1_PHOTO_ALT'), 
        'lp_imagem_dep_2_photo_url_file': ('LP_IMAGEM_DEP_2_PHOTO_URL', 'LP_IMAGEM_DEP_2_PHOTO_ALT'), 
        'lp_imagem_dep_3_photo_url_file': ('LP_IMAGEM_DEP_3_PHOTO_URL', 'LP_IMAGEM_DEP_3_PHOTO_ALT'), 
        'lp_link_pinterest_url_file': ('LP_LINK_PINTEREST', None), 
    }


    if request.method == 'POST':
        print(f"\n--- DEBUG: Requisição POST para salvar site {project.id} ---")
        
        final_content_for_injection = project.content_data.copy() if project.content_data else {}

        for file_input_name, (url_placeholder, alt_placeholder) in image_fields_map.items():
            if file_input_name in request.FILES:
                uploaded_file = request.FILES[file_input_name]
                try:
                    import uuid 
                    from django.core.files.storage import default_storage 
                    from django.core.files.base import ContentFile 

                    unique_filename = f"{slugify(os.path.splitext(uploaded_file.name)[0])}-{uuid.uuid4().hex[:8]}{os.path.splitext(uploaded_file.name)[1]}"
                    file_path = os.path.join('site_assets', str(project.id), unique_filename)
                    saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
                    uploaded_image_url = default_storage.url(saved_path)
                    
                    final_content_for_injection[url_placeholder] = uploaded_image_url
                    messages.success(request, f"Image '{uploaded_file.name}' uploaded successfully!")
                    print(f"DEBUG: File '{uploaded_file.name}' saved to: {uploaded_image_url}")
                    
                except Exception as e:
                    messages.error(request, f"Error uploading image {uploaded_file.name}: {e}")
                    print(f"!!! ERROR UPLOADING IMAGE: {e}")
            
            if alt_placeholder and alt_placeholder in request.POST:
                final_content_for_injection[alt_placeholder] = request.POST.get(alt_placeholder)


        for placeholder_key in placeholders:
            if placeholder_key not in [val[0] for val in image_fields_map.values()]:
                posted_value = request.POST.get(placeholder_key)
                if posted_value is not None:
                    final_content_for_injection[placeholder_key] = posted_value


        project.content_data = final_content_for_injection
        project.final_html_code = inject_content_into_html(project.base_html_code, final_content_for_injection)
        
        print(f"DEBUG: Final HTML Code generated (size): {len(project.final_html_code) if project.final_html_code else '0'}")
        
        try:
            project.save()
            messages.success(request, "Your site was saved successfully!")
            print(f"DEBUG: Project {project.id} saved to database. Redirecting...")
            return redirect('core:edit_site', project_id=project.id)
        except Exception as e:
            messages.error(request, f"Error saving project: {e}")
            print(f"!!! ERROR SAVING PROJECT: {e}")
            preview_html = inject_content_into_html(project.base_html_code, project.content_data)
            return render(request, 'core/edit_site.html', {
                'project': project,
                'placeholders': placeholders,
                'preview_html': preview_html
            })

    else: # GET request
        preview_html = inject_content_into_html(project.base_html_code, project.content_data)
        return render(request, 'core/edit_site.html', {
            'project': project,
            'placeholders': placeholders,
            'preview_html': preview_html
        })


@login_required
def preview_site_ajax(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(SiteProject, id=project_id, user=request.user)
        placeholders = extract_placeholders(project.base_html_code)
        
        import json 
        preview_content_data = json.loads(json.dumps(project.content_data)) if project.content_data else {}

        for key, value in request.POST.items():
            if not key.endswith('_FILE') and key in placeholders:
                preview_content_data[key] = value

        print(f"DEBUG PREVIEW AJAX: Final data for preview: {preview_content_data}")

        current_preview_html = inject_content_into_html(project.base_html_code, preview_content_data)
        
        print(f"DEBUG PREVIEW AJAX: Generated HTML for preview (first 1000 chars): {current_preview_html[:1000]}")

        return JsonResponse({'html': current_preview_html})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def download_site_view(request, project_id):
    project = get_object_or_404(SiteProject, id=project_id, user=request.user)

    print(f"\n--- DEBUG: Content of final_html_code for download (start):")
    print(project.final_html_code[:500] if project.final_html_code else "NO FINAL HTML CODE FOUND!")
    print("--- END DEBUG ---\n")

    if not project.final_html_code:
        messages.error(request, "The site does not have a final saved code. Please edit and save the site first.")
        return redirect('core:edit_site', project_id=project.id)
    
    file_name = slugify(project.name) + ".html"

    response = HttpResponse(project.final_html_code, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response


@login_required
@csrf_exempt # REMOVE THIS DECORATOR IN PRODUCTION!
def publish_site_view(request, project_id):
    project = get_object_or_404(SiteProject, id=project_id, user=request.user)

    if request.method == 'POST':
        if not project.final_html_code:
            print(f"DEBUG: publish_site_view - final_html_code is empty for project {project.id}")
            messages.error(request, "No final HTML code to publish. Save the site first.")
            return JsonResponse({'error': 'No final HTML code to publish. Save the site first.'}, status=400)

        temp_dir = None
        try:
            # Re-import docker here, as it's not global anymore and this function uses it.
            import docker
            import shutil
            import tempfile

            temp_dir = tempfile.mkdtemp()
            site_files_dir = os.path.join(temp_dir, 'site_content')
            os.makedirs(site_files_dir)
            
            index_html_path = os.path.join(site_files_dir, 'index.html')
            with open(index_html_path, 'w', encoding='utf-8') as f:
                f.write(project.final_html_code)
            
            print(f"DEBUG: HTML saved to {index_html_path}")

            dockerfile_source = os.path.join(settings.BASE_DIR, 'docker_templates', 'Dockerfile.static_site')
            dockerfile_dest = os.path.join(temp_dir, 'Dockerfile') # The Docker expects 'Dockerfile'
            shutil.copy(dockerfile_source, dockerfile_dest)
            
            print(f"DEBUG: Dockerfile copied to {docker_dest}")

            client = docker.from_env()

            image_name = f"gayapublishedsite-{project.id}".lower()
            
            print(f"DEBUG: Starting Docker image build for '{image_name}' from context '{temp_dir}'...")
            image, build_logs = client.images.build(
                path=temp_dir,
                dockerfile=os.path.basename(dockerfile_dest),
                tag=image_name,
                rm=True
            )
            print(f"DEBUG: Docker image '{image.tags[0]}' built successfully!")
            
            published_path = reverse('core:view_published_site', args=[project.id])
            project.published_url = request.build_absolute_uri(published_path)
            project.save()
            
            messages.success(request, f"Site '{project.name}' published successfully! Access it at: <a href='{project.published_url}' target='_blank'>{project.published_url}</a>")
            print(f"DEBUG: Site {project.id} published at: {project.published_url}")
            
            return JsonResponse({'success': True, 'published_url': project.published_url})

        except docker.errors.BuildError as e:
            error_message = f"Error building Docker image: {e}. Check if Docker is running and Dockerfile is correct."
            messages.error(request, error_message)
            print(f"ERROR DOCKER BUILD: {e}")
            return JsonResponse({'error': error_message}, status=500)
        except Exception as e:
            error_message = f"Unexpected error in publication (check Docker or permissions): {e}."
            messages.error(request, error_message)
            print(f"GENERAL PUBLICATION ERROR (DOCKER CONNECTION/GENERAL): {e}")
            return JsonResponse({'error': error_message}, status=500)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"DEBUG: Temporary directory {temp_dir} removed.")
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def view_published_site(request, project_id):
    project = get_object_or_404(SiteProject, id=project_id)

    if project.final_html_code:
        return HttpResponse(project.final_html_code, content_type='text/html')
    else:
        return HttpResponse("<h1>Site not found or not published.</h1><p>Please publish the site first.</p>", status=404)


@login_required
def my_sites_view(request):
    user_projects = SiteProject.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/my_sites.html', {'user_projects': user_projects})

def contact_view(request):
    return render(request, 'core/contact.html')