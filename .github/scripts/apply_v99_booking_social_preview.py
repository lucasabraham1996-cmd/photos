from pathlib import Path
p=Path('contrataciones.html')
s=p.read_text(encoding='utf-8')
needle='  <meta name="theme-color" content="#050505" />\n'
if needle not in s:
    raise SystemExit('theme-color marker not found')
block='''  <meta name="theme-color" content="#050505" />
  <meta name="description" content="Reservá tu cobertura fotográfica deportiva con lucasabraham.ph." />
  <meta property="og:locale" content="es_AR" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="lucasabraham.ph" />
  <meta property="og:title" content="Reservá tu cobertura · lucasabraham.ph" />
  <meta property="og:description" content="Completá los datos del partido y confirmá tu cobertura fotográfica." />
  <meta property="og:image" content="https://lucasabraham1996-cmd.github.io/photos/social-preview-la.png?v=99" />
  <meta property="og:image:secure_url" content="https://lucasabraham1996-cmd.github.io/photos/social-preview-la.png?v=99" />
  <meta property="og:image:type" content="image/png" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content="lucasabraham.ph · Fotografía deportiva" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Reservá tu cobertura · lucasabraham.ph" />
  <meta name="twitter:description" content="Completá los datos del partido y confirmá tu cobertura fotográfica." />
  <meta name="twitter:image" content="https://lucasabraham1996-cmd.github.io/photos/social-preview-la.png?v=99" />
'''
# Avoid duplicates if rerun.
if 'property="og:image"' in s:
    raise SystemExit('Open Graph tags already exist')
s=s.replace(needle,block,1)
p.write_text(s,encoding='utf-8')
print('v99 booking social preview patched')
