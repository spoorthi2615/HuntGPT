import json

for split in ['train', 'val', 'test']:
    data = json.load(open(f'data/injection_corpus/{split}.json'))
    injected = sum(1 for d in data if d['label'] == 1)
    print(f'{split}: {len(data)} samples, {injected} injected ({injected/len(data)*100:.1f}%)')
