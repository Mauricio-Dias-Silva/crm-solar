import os
import shutil
import tempfile
import docker # Certifique-se de ter 'pip install docker'

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils.text import slugify
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt 
from django.contrib import messages # Importe messages (necessário para exibir mensagens na UI)

from .models import SiteProject
from .utils import extract_placeholders, inject_content_into_html # Removed add_editable_attributes if not used

import google.api_core.exceptions # Necessário para capturar erros específicos do Gemini
import json # Necessário para json.loads(json.dumps()) na preview_site_ajax
import uuid # Necessário para nomes de arquivo únicos no upload
from django.core.files.storage import default_storage # Necessário para upload de arquivos
from django.core.files.base import ContentFile # Necessário para upload de arquivos


# --- AI CLIENT INITIALIZATION (ONLY ONCE AT THE TOP OF THE MODULE) ---
openai_client = None
if settings.OPENAI_API_KEY:
    try:
        import openai
        openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        print("OpenAI client initialized successfully.")
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")

gemini_model = None
if settings.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('models/gemini-1.5-flash')
        print("Gemini model 'models/gemini-1.5-flash' initialized successfully.")
    except Exception as e:
        print(f"*** CRITICAL ERROR INITIALIZING GEMINI MODEL: {e} ***")
        print("Check if your GEMINI_API_KEY is correct and has permissions.")
        gemini_model = None
# --- END AI client initialization ---

# --- VIEWS ---

def home_view(request):
    return render(request, 'core/home.html')

@login_required
def create_site_view(request):
    generated_code = None
    user_prompt_input = None
    error_message = None

    selected_ai_provider = settings.DEFAULT_AI_PROVIDER

    # --- DEFINIÇÃO DOS PROMPTS AI (NO INÍCIO DA FUNÇÃO create_site_view para garantir escopo) ---
    ai_system_prompt = (
        "You are an experienced static landing page designer and front-end developer, highly skilled in HTML5, CSS3 (with a focus on Bootstrap 5 classes for responsiveness) and minimalist JavaScript. "
        "Your mission is to create visually stunning, intuitive, and highly responsive landing pages for various niches. "
        "Strictly follow modern UI/UX principles: prioritize clear visual hierarchy, adequate spacing (padding and margin) for readability, harmonious color palettes (complementary and/or analogous), clean and legible typography (avoiding excessive fonts), and smooth transitions for a fluid experience."
        "Responsive Design: Ensure the layout is impeccable across all devices (desktop, tablet, mobile) using Bootstrap 5's grid classes and responsiveness utilities."
        "Visual Creativity: Don't limit yourself to generic layouts. Think about creating visually interesting sections, with complementary backgrounds, subtle use of shadows, rounded corners, and hover effects for buttons and links (CSS only). Incorporate a style that conveys the essence of the user's description."
        "Code Structure: The code must be semantic (using `<header>`, `<main>`, `<section>`, `<footer>`, etc.), well-commented, and easy to understand. Include the CSS in a `<style>` block in the `<head>` (for page-specific styles) and reference Bootstrap via CDN."
        "Use the following EXACT placeholders for user-editable content. Insert these placeholders directly into the HTML:"
        "`[LP_HERO_TITULO]`, `[LP_HERO_SUBTITULO]`, `[LP_HERO_CTA_TEXTO]`, `[LP_HERO_CTA_LINK]`, "
        "`[LP_BENEFICIO_1_TITULO]`, `[LP_BENEFICIO_1_DESCRICAO]`, `[LP_BENEFICIO_2_TITULO]`, `[LP_BENEFICIO_2_DESCRICAO]`, `[LP_BENEFICIO_3_TITULO]`, `[LP_BENEFICIO_3_DESCRICAO]`, "
        "`[DEP_1_TEXTO]`, `[DEP_1_NOME]`, `[DEP_2_TEXTO]`, `[DEP_2_NOME]`, `[DEP_3_TEXTO]`, `[DEP_3_NOME]`, "
        "`[FORM_TITULO]`, `[FORM_SUBMIT_TEXTO]`, "
        "`[LP_RODAPE_COPYRIGHT]`, `[LP_LINK_FACEBOOK]`, `[LP_LINK_INSTAGRAM]`. "
        "For content images (such as in galleries, profiles, or within benefit/feature sections), generate the `<img>` tag with an `src` placeholder as follows: "
        "`<img src=\"[LP_IMAGEM_SECAO_NOME_URL]\" alt=\"[LP_IMAGEM_SECAO_NOME_ALT]\" class=\"img-fluid\">`. "
        "Replace 'SECAO_NOME' and 'NOME' with something descriptive like 'GALLERY_1', 'BENEFIT_1', 'DEP_1_PHOTO'. "
        "If there's a background image in the hero section, use `background-image: url('[LP_HERO_BG_IMAGEM_URL]');` directly in the CSS. "
        "Generate at least 3 content image placeholders and 1 for the Hero Section background image, if applicable to the context. "
        "DO NOT include PHP, Python backend, or any server-side scripts. JavaScript should be minimal, only for front-end functionalities (e.g., Bootstrap carousels, scroll effects, simple contact form that can be configured via Formspree or similar if there's a placeholder for an action URL)."
        "Return ONLY the complete and renderable HTML code, without any introductory text, explanations, or extra markdown like ```html."
    )
    # ai_user_prompt é definido abaixo, dentro do if request.method == 'POST',
    # pois ele depende do user_prompt_input.
    # Para o caso de GET request, ou se ele for usado antes, use um valor padrão.
    ai_user_prompt = "Generate a simple placeholder for a landing page." # Valor padrão para garantir que sempre exista.


    if request.method == 'POST':
        user_prompt_input = request.POST.get('prompt')

        # Atualiza ai_user_prompt com o input real do usuário AQUI
        ai_user_prompt = (
            f"Generate a landing page based on the following description: '{user_prompt_input}'. "
            "The page should be visually appealing and follow the latest design trends. "
            "Include the sections: Hero, 3 Benefits, 3 Testimonials, Contact Form, and Footer. "
            "The design should be modern and clean, with intelligent use of colors and spacing to improve readability and aesthetics. "
            "Think of a professional color scheme and pleasant typography. "
            "If the description implies a specific visual style, incorporate it. "
            "Keep it generic for TEXT placeholders and use IMAGE placeholders according to system instructions."
        )


        if not user_prompt_input:
            error_message = "Por favor, forneça uma descrição para o site."
            return render(request, 'core/create_site.html', {
                'generated_code': generated_code,
                'user_prompt': user_prompt_input,
                'error_message': error_message
            })

        # --- INÍCIO DO BLOCO DE GERAÇÃO DA IA ---
        try:
            print(f"Tentando gerar conteúdo usando {selected_ai_provider}...")
            if selected_ai_provider == "gemini" and gemini_model:
                response = gemini_model.generate_content(
                    [ai_system_prompt, ai_user_prompt], # ai_system_prompt e ai_user_prompt estão definidos agora
                    generation_config=genai.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=2000
                    ),
                    request_options={'timeout': 120}
                )
                generated_code = response.text
            elif selected_ai_provider == "openai" and openai_client:
                response = openai_client.chat.completions.create(
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
                print(error_message)
                return render(request, 'core/create_site.html', {
                    'generated_code': generated_code,
                    'user_prompt': user_prompt_input,
                    'error_message': error_message
                })

            if generated_code and generated_code.strip().startswith("```") and generated_code.strip().endswith("```"):
                generated_code = generated_code.replace("```html\n", "").replace("```\n", "").strip()
                generated_code = generated_code.replace("```html", "").replace("```", "").strip()

            if generated_code and len(generated_code.strip()) > 100 and "<html" in generated_code.lower() and "<head" in generated_code.lower() and "<body" in generated_code.lower():
                print(f"\n--- DEBUG: Generated AI code (start):")
                print(generated_code[:500])
                print("--- END DEBUG ---\n")

                processed_html_code = generated_code 

                initial_project_name = f"LP - {user_prompt_input[:70]}{'...' if len(user_prompt_input) > 70 else ''}"
                project = SiteProject.objects.create(
                    user=request.user,
                    original_prompt=user_prompt_input,
                    base_html_code=processed_html_code,
                    name=initial_project_name,
                    content_data={} 
                )
                print(f"Project {project.id} saved! Redirecting to edit...")
                return redirect('edit_site', project_id=project.id)
            else:
                error_message = "O código gerado pela IA é inválido ou muito curto. Por favor, tente um prompt diferente ou ajuste os parâmetros da IA."
                print(f"AI generated code invalid or too short. Generated code length: {len(generated_code.strip()) if generated_code else 0}")
                print(f"Generated Code: {generated_code[:200] if generated_code else 'None'}")

        except google.api_core.exceptions.GoogleAPIError as e:
            error_message = f"Erro da API Gemini: {e}. Status: {getattr(e, 'response', None)}. Verifique a chave API, permissões ou limites de taxa."
            print(f"!!! ERRO DA API GEMINI: {e} !!!")
        except Exception as e:
            error_message = f"Erro durante a Geração/Pós-processamento da IA ({selected_ai_provider}): {e}. Por favor, verifique os logs do servidor."
            print(f"!!! ERRO FATAL NA GERAÇÃO/PÓS-PROCESSAMENTO ({selected_ai_provider}): {e}")
        # --- FIM DO BLOCO DE GERAÇÃO DA IA ---

        # Este é o retorno final para POST requests que não resultaram em redirecionamento (ou seja, houve um erro)
        return render(request, 'core/create_site.html', {
            'generated_code': generated_code,
            'user_prompt': user_prompt_input,
            'error_message': error_message
        })

    # Este é o retorno para GET requests (quando a página é acessada diretamente pela primeira vez)
    return render(request, 'core/create_site.html', {
        'generated_code': generated_code,
        'user_prompt': user_prompt_input,
        'error_message': error_message
    })


@login_required
def edit_site_view(request, project_id):
    project = get_object_or_404(SiteProject, id=project_id, user=request.user)
    placeholders = extract_placeholders(project.base_html_code)

    if request.method == 'POST':
        print(f"\n--- DEBUG: POST request received to save site {project.id} ---")
        content_data = {}
        
        # Mapeamento dos campos de upload de arquivo para seus placeholders de URL e ALT
        image_fields_map = {
            'LP_HERO_BG_IMAGEM_URL_FILE': ('LP_HERO_BG_IMAGEM_URL', 'LP_HERO_BG_IMAGEM_ALT'),
            'LP_IMAGEM_BENEFIT_1_URL_FILE': ('LP_IMAGEM_BENEFIT_1_URL', 'LP_IMAGEM_BENEFIT_1_ALT'),
            'LP_IMAGEM_BENEFIT_2_URL_FILE': ('LP_IMAGEM_BENEFIT_2_URL', 'LP_IMAGEM_BENEFIT_2_ALT'),
            'LP_IMAGEM_BENEFIT_3_URL_FILE': ('LP_IMAGEM_BENEFIT_3_URL', 'LP_IMAGEM_BENEFIT_3_ALT'),
            'LP_IMAGEM_DEP_1_PHOTO_URL_FILE': ('LP_IMAGEM_DEP_1_PHOTO_URL', 'LP_IMAGEM_DEP_1_PHOTO_ALT'),
            'LP_IMAGEM_DEP_2_PHOTO_URL_FILE': ('LP_IMAGEM_DEP_2_PHOTO_URL', 'LP_IMAGEM_DEP_2_PHOTO_ALT'),
            'LP_IMAGEM_DEP_3_PHOTO_URL_FILE': ('LP_IMAGEM_DEP_3_PHOTO_URL', 'LP_IMAGEM_DEP_3_PHOTO_ALT'),
        }

        # Processar uploads de arquivos primeiro
        for file_input_name, (url_placeholder, alt_placeholder) in image_fields_map.items():
            if file_input_name in request.FILES:
                uploaded_file = request.FILES[file_input_name]
                try:
                    unique_filename = f"{slugify(os.path.splitext(uploaded_file.name)[0])}-{uuid.uuid4().hex[:8]}{os.path.splitext(uploaded_file.name)[1]}"
                    
                    file_path = os.path.join('site_assets', str(project.id), unique_filename)
                    saved_path = default_storage.save(file_path, ContentFile(uploaded_file.read()))
                    
                    uploaded_image_url = default_storage.url(saved_path)
                    
                    content_data[url_placeholder] = uploaded_image_url
                    print(f"DEBUG: Arquivo '{uploaded_file.name}' salvo em: {uploaded_image_url}")
                    
                except Exception as e:
                    messages.error(request, f"Erro ao fazer upload da imagem {uploaded_file.name}: {e}")
                    print(f"!!! ERRO UPLOAD IMAGEM: {e}")
            
            if alt_placeholder in request.POST:
                content_data[alt_placeholder] = request.POST.get(alt_placeholder)


        final_content_for_injection = project.content_data.copy() if project.content_data else {}

        for placeholder_key in placeholders:
            posted_value = request.POST.get(placeholder_key)
            
            if placeholder_key in content_data:
                final_content_for_injection[placeholder_key] = content_data[placeholder_key]
            elif posted_value is not None:
                final_content_for_injection[placeholder_key] = posted_value


        project.content_data = final_content_for_injection
        project.final_html_code = inject_content_into_html(project.base_html_code, final_content_for_injection)
        
        print(f"DEBUG: Final HTML Code generated (size): {len(project.final_html_code) if project.final_html_code else '0'}")
        
        try:
            project.save()
            messages.success(request, "Seu site foi salvo com sucesso!")
            print(f"DEBUG: Project {project.id} saved to database. Redirecting...")
            return redirect('edit_site', project_id=project.id)
        except Exception as e:
            messages.error(request, f"Erro ao salvar o projeto: {e}")
            print(f"!!! ERRO AO SALVAR PROJETO: {e}")
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

# core/views.py - Apenas o trecho da função preview_site_ajax

@login_required
def preview_site_ajax(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(SiteProject, id=project_id, user=request.user)
        
        # 1. Começa com uma CÓPIA PROFUNDA dos dados JÁ SALVOS no projeto.
        # ISSO É CRÍTICO para que as URLs de imagens que já foram salvas persistam no preview.
        import json
        preview_content_data = json.loads(json.dumps(project.content_data)) if project.content_data else {}

        # 2. Itere sobre os dados enviados pelo formulário (via AJAX POST).
        # Estes são os valores MAIS RECENTES (digitados pelo usuário nos campos de TEXTO/URL).
        # Eles SOBREPÕEM os valores correspondentes em preview_content_data.
        for key, value in request.POST.items():
            # Apenas atualize se a 'key' for um placeholder que esperamos.
            # (Os campos _FILE não vêm via request.POST, então não serão incluídos aqui.)
            if key in extract_placeholders(project.base_html_code):
                preview_content_data[key] = value
            # Para o caso dos ALT texts de imagem (que são campos de texto no HTML)
            # certificamos que sejam atualizados se estiverem nos dados POST
            elif key.endswith('_ALT') and key in extract_placeholders(project.base_html_code):
                 preview_content_data[key] = value


        # Adiciona um tratamento especial para URLs de imagem que podem não ter sido explicitamente
        # listadas em request.POST. Se a imagem foi salva anteriormente, sua URL está em project.content_data.
        # Percorrer o image_fields_map para garantir que as URLs já salvas sejam mantidas se não houve novo POST.
        # No seu edit_site_view, você tem o image_fields_map. Vamos replicar os placeholders de URL.
        # IMPORTANTE: Garanta que esta lista de placeholders de URL esteja completa e correta.
        image_url_placeholders = [
            'LP_HERO_BG_IMAGEM_URL',
            'LP_IMAGEM_BENEFIT_1_URL',
            'LP_IMAGEM_BENEFIT_2_URL',
            'LP_IMAGEM_BENEFIT_3_URL',
            'LP_IMAGEM_DEP_1_PHOTO_URL',
            'LP_IMAGEM_DEP_2_PHOTO_URL',
            'LP_IMAGEM_DEP_3_PHOTO_URL',
        ]
        
        for img_url_key in image_url_placeholders:
            # Se a URL de imagem *não foi enviada* no POST (porque não é um campo de texto ou link),
            # mas EXISTE no project.content_data (porque já foi salva),
            # então use a URL salva para o preview.
            if img_url_key not in request.POST and img_url_key in project.content_data:
                preview_content_data[img_url_key] = project.content_data[img_url_key]
            # Se a URL de imagem *foi enviada* no POST (ex: era um campo de texto para URL),
            # então o loop acima já a colocou em preview_content_data.
            # Se o campo de imagem for um `input type="file"`, ele não virá no `request.POST`,
            # então a lógica acima que prioriza `project.content_data` para valores não postados
            # é a que fará a URL da imagem salva aparecer.

        # DEBUGGING: Imprima os dados finais que serão passados para a injeção
        print(f"DEBUG PREVIEW AJAX: Dados finais para preview: {preview_content_data}")

        # 3. Gera o HTML para pré-visualização com os dados mesclados
        current_preview_html = inject_content_into_html(project.base_html_code, preview_content_data)
        
        # DEBUGGING: Imprima o HTML gerado para preview (apenas o início)
        # Verifique se os placeholders de imagem foram substituídos aqui
        print(f"DEBUG PREVIEW AJAX: HTML gerado para preview (primeiros 1000 chars): {current_preview_html[:1000]}")

        return JsonResponse({'html': current_preview_html})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def download_site_view(request, project_id):
    project = get_object_or_404(SiteProject, id=project_id, user=request.user)
    print(f"\n--- DEBUG: Content of final_html_code for download (start):")
    print(project.final_html_code[:500] if project.final_html_code else "NO FINAL HTML CODE FOUND!")
    print("--- END DEBUG ---\n")
    if not project.final_html_code:
        return redirect('edit_site', project_id=project.id)
    file_name = slugify(project.name or f"site-project-{project.id}") + ".html"
    response = HttpResponse(project.final_html_code, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response

@login_required
@csrf_exempt
def publish_site_view(request, project_id):
    project = get_object_or_404(SiteProject, id=project_id, user=request.user)
    if request.method == 'POST':
        if not project.final_html_code:
            print(f"DEBUG: publish_site_view - final_html_code is empty for project {project.id}")
            return JsonResponse({'error': 'No final HTML code to publish. Save the site first.'}, status=400)
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            site_files_dir = os.path.join(temp_dir, 'site_content')
            os.makedirs(site_files_dir)
            index_html_path = os.path.join(site_files_dir, 'index.html')
            with open(index_html_path, 'w', encoding='utf-8') as f:
                f.write(project.final_html_code)
            print(f"DEBUG: HTML saved to {index_html_path}")
            dockerfile_source = os.path.join(settings.BASE_DIR, 'docker_templates', 'Dockerfile.static_site')
            dockerfile_dest = os.path.join(temp_dir, 'Dockerfile')
            shutil.copy(dockerfile_source, dockerfile_dest)
            print(f"DEBUG: Dockerfile copied to {dockerfile_dest}")
            client = docker.from_env()
            image_name = f"gayapublishedsite-{project.id}-{slugify(project.name or 'anon')}".lower()
            image_name = image_name[:100].strip('-')
            print(f"DEBUG: Starting Docker image build for '{image_name}' from context '{temp_dir}'...")
            image, build_logs = client.images.build(
                path=temp_dir,
                dockerfile=os.path.basename(dockerfile_dest),
                tag=image_name,
                rm=True
            )
            for line in build_logs:
                if 'stream' in line:
                    print(line['stream'].strip())
            print(f"DEBUG: Docker image '{image.tags[0]}' built successfully!")
            published_path = reverse('view_published_site', args=[project.id])
            project.published_url = request.build_absolute_uri(published_path)
            project.save()
            print(f"DEBUG: Site {project.id} 'publicado' (URL interna) em: {project.published_url}")
            return JsonResponse({'success': True, 'published_url': project.published_url})
        except docker.errors.BuildError as e:
            error_logs = ""
            if e.build_log:
                for line in e.build_log:
                    if 'stream' in line:
                        error_logs += line['stream']
            print(f"ERROR DOCKER BUILD: {e}\nLogs: {error_logs}")
            return JsonResponse({'error': f'Error building Docker image: {e}. Verifique os logs para mais detalhes.'}, status=500)
        except docker.errors.APIError as e:
            print(f"ERRO DE API DOCKER: {e}")
            return JsonResponse({'error': f'Erro na comunicação com o Docker (API Error): {e}. Certifique-se de que o Docker está em execução.'}, status=500)
        except Exception as e:
            print(f"GENERAL PUBLICATION ERROR (DOCKER CONNECTION/GENERAL): {e}")
            return JsonResponse({'error': f'Unexpected error in publication (check Docker): {e}'}, status=500)
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