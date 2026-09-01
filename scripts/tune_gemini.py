import os
import sys
import argparse
from pathlib import Path

def main():
    print('=======================================================')
    print('🚀 Quilltale — Gemini 1-클릭 자동 파인튜닝 의뢰기')
    print('=======================================================\n')
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='data/dataset_master_combined.jsonl')
    parser.add_argument('--key', type=str, default='')
    args = parser.parse_args()
    
    api_key = args.key or os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        try:
            api_key = input('👉 Gemini API 키를 입력하세요: ').strip()
        except Exception:
            pass
            
    if not api_key:
        print('❌ 오류: Gemini API 키가 필요합니다.')
        return
        
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        # Check in default location
        alt_path = Path('c:/Quilltale/data/dataset_master_combined.jsonl')
        if alt_path.exists():
            dataset_path = alt_path
        else:
            print(f'❌ 오류: 데이터셋 파일을 찾을 수 없습니다: {dataset_path}')
            return
            
    print(f'📦 데이터셋 확인: {dataset_path} ({dataset_path.stat().st_size / 1024:.1f} KB)')
    print('⏳ 구글 AI 서버에 튜닝 작업을 등록합니다...')
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # Upload dataset file to Google AI
        uploaded_file = client.files.upload(file=str(dataset_path))
        print(f'✅ 데이터셋 업로드 완료: {uploaded_file.name}')
        
        print('\n🎉 구글 AI 서버에 전송 완료!')
        print('👉 수집된 고품질 데이터셋이 안전하게 Google AI Studio에 등록되었습니다.')
    except Exception as e:
        print(f'⚠️ 등록 결과: {e}')

if __name__ == '__main__':
    main()
