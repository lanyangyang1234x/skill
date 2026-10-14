from pathlib import Path
import importlib.util, tempfile, shutil, json, zipfile
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('vendorcheck',root/'scripts/verify_chinese_writing_vendor.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results=[]
def run(name,edit=None,expect='failed'):
    with tempfile.TemporaryDirectory(prefix='chinese-writing-vendor-test-') as d:
        p=Path(d);shutil.copytree(root/'vendor',p/'vendor')
        if edit: edit(p)
        result=m.verify(p)
        assert result['status']==expect,(name,result)
        results.append({'case':name,'expected':expect,'actual':result['status'],'errors':result['errors']})
run('pristine',expect='passed')
run('tampered-method',lambda p:(p/'vendor/chinese-writing/references/qualification.md').write_text('tampered'))
run('missing-method',lambda p:(p/'vendor/chinese-writing/LICENSE').unlink())
run('extra-method',lambda p:(p/'vendor/chinese-writing/extra.md').write_text('extra'))
run('standalone-skill-entry',lambda p:(p/'vendor/chinese-writing/SKILL.md').write_text('---\nname: chinese-writing\n---'))
run('agent-guidance',lambda p:(p/'vendor/chinese-writing/AGENTS.md').write_text('guidance'))
run('missing-archive',lambda p:(p/'vendor/chinese-writing-upstream.zip').unlink())
run('bad-archive',lambda p:(p/'vendor/chinese-writing-upstream.zip').write_bytes(b'not a zip'))
run('invalid-lock',lambda p:(p/'vendor/chinese-writing.lock.json').write_text('{'))
def alter_lock(p):
    f=p/'vendor/chinese-writing.lock.json';v=json.loads(f.read_text());v['files']['../escape']=v['files']['LICENSE'];f.write_text(json.dumps(v))
run('unsafe-runtime-lock-path',alter_lock)
def badmember(p):
    import hashlib
    archive=p/'vendor/chinese-writing-upstream.zip'
    with zipfile.ZipFile(archive,'a') as z:z.writestr('../escape','escape')
    f=p/'vendor/chinese-writing.lock.json';v=json.loads(f.read_text());v['upstream_archive']['bytes']=archive.stat().st_size;v['upstream_archive']['sha256']=hashlib.sha256(archive.read_bytes()).hexdigest();f.write_text(json.dumps(v))
run('unsafe-archive-member-even-with-updated-container-hash',badmember)
print(f'{len(results)} vendor checks passed')
