import os.path

from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse, HttpResponseNotFound
from django.shortcuts import render

from openai_translator_ui import settings
from openai_translator_ui.ai_translator.model import OpenAIModel
from openai_translator_ui.ai_translator.translator import PDFTranslator


# Create your views here.

def index(request):
    return render(request, "index.html")


def handle_translate(request):
    try:
        if request.method == 'POST':
            # 获取API Key
            api_key = request.POST.get('apiKey')

            # print(request.body)

            # 检查API Key是否为空
            if not api_key:
                return JsonResponse({'status': 'error', 'message': 'API Key不能为空'}, status=400)
            else:
                api_key = api_key.strip()

            out_format = request.POST.get('format')
            if not out_format:
                return JsonResponse({'status': 'error', 'message': '输出格式不能为空'}, status=400)

            model_name = request.POST.get('model')
            if not model_name:
                return JsonResponse({'status': 'error', 'message': '模型不能为空'}, status=400)

            language = request.POST.get('language')
            if not language:
                return JsonResponse({'status': 'error', 'message': '语言不能为空'}, status=400)

            # 获取上传的文件
            uploaded_file = request.FILES.get('file')

            # 检查文件是否存在和类型
            if uploaded_file is None or uploaded_file.content_type != 'application/pdf':
                return JsonResponse({'status': 'error', 'message': '只接受PDF文件上传'}, status=400)

            print(
                f'filename={uploaded_file.name}, key={api_key}, model={model_name}, language={language}, format={out_format}')
            # 获取文件名
            # 创建一个FileSystemStorage实例
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)

            # 保存文件到MEDIA_ROOT目录
            filename = fs.save(uploaded_file.name, uploaded_file)

            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            # translate
            model = OpenAIModel(model=model_name, api_key=api_key)
            translator = PDFTranslator(model)
            success, out_path = translator.translate_pdf(file_path, out_format, language)

            # 返回成功的响应
            if success:
                response_data = {'status': 'success', 'filename': os.path.basename(out_path)}
                return JsonResponse(response_data)
            else:
                response_data = {'status': 'error', 'message': out_path}
                return JsonResponse(response_data, status=500)
        else:
            # GET请求或其他请求，返回错误提示或重定向至其他页面
            return HttpResponseNotAllowed(['POST'])
    except Exception as e:
        print('Internal error: ', str(e))
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def handle_download(request):
    try:
        if request.method == 'GET':
            filename = request.GET.get('filename')
            if not filename:
                return JsonResponse({'status': 'error', 'message': 'filename不能为空'}, status=400)
            else:
                filename = filename.strip('"')
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(os.path.basename(file_path))
            return response
    except FileNotFoundError:
        return HttpResponseNotFound("文件未找到")
    except Exception as e:
        print('Internal error: ', str(e))
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
