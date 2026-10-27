"""Gera 02_dados.sql (INSERTs em lote) para o banco rede_americas_ontologia. Dados 100% sintéticos, seed fixa.

Histórias plantadas (cada uma só aparece cruzando domínios):
  O1  Beta (OP02) passa a negar RM de joelho, artroscopia e artroplastia a partir de mai/2026. Parte dos pacientes é
      atendida mesmo assim: a conta volta com glosa "sem autorização prévia" e a central recebe reclamações
      (protocolo → autorização → atendimento → conta → item → glosa).
  O2  Dr. Ricardo Menezes Prado (ortopedia, Hospital Américas Sul) cobra OPME 25% acima do preço contratado desde
      fev/2026 → glosas "valor acima do contratado" (médico → item → preço contratado → glosa).
  O3  Beneficiários do plano Delta Essencial (enfermaria) internados no Hospital Américas Centro recebem diária de
      apartamento em ~40% das internações → glosa de acomodação e reclamação de cobrança na central
      (paciente → beneficiário → plano → item → glosa → protocolo).
Uso: python3 gerar_dados.py  (escreve 02_dados.sql ao lado)"""
import datetime as dt
import math
import random
from collections import defaultdict
from pathlib import Path

R = random.Random(42)
INICIO, HOJE = dt.date(2025, 11, 1), dt.date(2026, 10, 26)
AGORA = dt.datetime(2026, 10, 26, 9, 0)
SAIDA = Path(__file__).with_name("02_dados.sql")

# ------------------------------------------------------------------ cadastros fixos
UNIDADES = [("U01", "Hospital Américas Centro", "HOSPITAL", "São Paulo", "SP", 320),
            ("U02", "Hospital Américas Sul", "HOSPITAL", "Curitiba", "PR", 180),
            ("U03", "Centro Oncológico Américas", "ONCOLOGIA", "São Paulo", "SP", 40),
            ("U04", "Ambulatório Américas Paulista", "AMBULATORIO", "São Paulo", "SP", None)]
ESPECIALIDADES = [("EMG", "Emergência"), ("CLI", "Clínica médica"), ("ORT", "Ortopedia"), ("CAR", "Cardiologia"),
                  ("CIR", "Cirurgia geral"), ("GIN", "Ginecologia"), ("NEU", "Neurologia"), ("ONC", "Oncologia")]
OPERADORAS = [("OP01", "Alfa Saúde", "312045", 30), ("OP02", "Beta Assistência Médica", "326577", 30),
              ("OP03", "Gama Saúde", "359017", 45), ("OP04", "Delta Assistência", "301337", 60),
              ("OP05", "Épsilon Seguros Saúde", "005711", 30)]
FATOR_OP = {"OP01": 1.00, "OP02": 0.95, "OP03": 1.05, "OP04": 0.92, "OP05": 1.10}
PLANOS = [("ALF-ESS", "OP01", "Alfa Essencial", "HOSPITALAR", "ENFERMARIA"),
          ("ALF-PRE", "OP01", "Alfa Premium", "REFERENCIA", "APARTAMENTO"),
          ("BET-CLA", "OP02", "Beta Clássico", "HOSPITALAR", "ENFERMARIA"),
          ("BET-EXE", "OP02", "Beta Executivo", "REFERENCIA", "APARTAMENTO"),
          ("GAM-SEL", "OP03", "Gama Seleto", "HOSPITALAR", "APARTAMENTO"),
          ("GAM-BAS", "OP03", "Gama Básico", "HOSPITALAR", "ENFERMARIA"),
          ("DEL-ESS", "OP04", "Delta Essencial", "HOSPITALAR", "ENFERMARIA"),
          ("DEL-MAS", "OP04", "Delta Master", "REFERENCIA", "APARTAMENTO"),
          ("EPS-TOP", "OP05", "Épsilon Top", "REFERENCIA", "APARTAMENTO"),
          ("EPS-FLX", "OP05", "Épsilon Flex", "HOSPITALAR", "ENFERMARIA")]
PESO_PLANO = {"ALF-ESS": 16, "ALF-PRE": 12, "BET-CLA": 13, "BET-EXE": 11, "GAM-SEL": 9, "GAM-BAS": 11,
              "DEL-ESS": 10, "DEL-MAS": 6, "EPS-TOP": 7, "EPS-FLX": 5}
PROCEDIMENTOS = [  # código, descrição, grupo, exige autorização, preço base
    ("10101012", "Consulta em consultório", "CONSULTA", 0, 180),
    ("10101039", "Consulta em pronto-socorro", "CONSULTA", 0, 250),
    ("40304361", "Hemograma completo", "EXAME", 0, 25),
    ("40901114", "Radiografia de tórax", "EXAME", 0, 60),
    ("41001010", "Tomografia computadorizada de crânio", "EXAME", 0, 650),
    ("41101014", "Ressonância magnética de joelho", "EXAME", 1, 1100),
    ("40901300", "Ultrassonografia de abdome total", "EXAME", 0, 180),
    ("40801020", "Ecocardiograma transtorácico", "EXAME", 0, 320),
    ("30725046", "Artroscopia de joelho (meniscectomia)", "PROCEDIMENTO", 1, 4200),
    ("30724040", "Artroplastia total de joelho", "PROCEDIMENTO", 1, 9500),
    ("30912016", "Angioplastia coronariana com implante de stent", "PROCEDIMENTO", 1, 7800),
    ("31005497", "Colecistectomia videolaparoscópica", "PROCEDIMENTO", 1, 3900),
    ("31009166", "Herniorrafia inguinal", "PROCEDIMENTO", 1, 2400),
    ("31303080", "Histerectomia total", "PROCEDIMENTO", 1, 4100),
    ("20104219", "Sessão de quimioterapia", "PROCEDIMENTO", 1, 950),
    ("70000101", "Prótese total de joelho", "OPME", 1, 18000),
    ("70000202", "Stent farmacológico", "OPME", 1, 9000),
    ("70000303", "Kit de âncoras e parafusos para artroscopia", "OPME", 1, 3200),
    ("60000101", "Kit de materiais cirúrgicos", "MATERIAL", 0, 850),
    ("60000102", "Materiais de pronto-socorro", "MATERIAL", 0, 120),
    ("60000103", "Materiais de enfermagem (diário)", "MATERIAL", 0, 140),
    ("90000101", "Medicamentos de pronto-socorro", "MEDICAMENTO", 0, 90),
    ("90000102", "Antibiótico endovenoso (dose)", "MEDICAMENTO", 0, 210),
    ("90000103", "Antineoplásico (ciclo)", "MEDICAMENTO", 1, 6800),
    ("90000104", "Medicação de internação (diária)", "MEDICAMENTO", 0, 260),
    ("80000101", "Diária de enfermaria", "DIARIA", 0, 900),
    ("80000102", "Diária de apartamento", "DIARIA", 0, 1450),
    ("80000103", "Diária de UTI adulto", "DIARIA", 0, 3800),
    ("85000101", "Taxa de sala cirúrgica", "TAXA", 0, 1200),
    ("85000102", "Taxa de sala de observação", "TAXA", 0, 180),
    ("85000103", "Taxa de sala de quimioterapia", "TAXA", 0, 320)]
PROC = {p[0]: p for p in PROCEDIMENTOS}
CIDS = [("J06.9", "Infecção aguda das vias aéreas superiores", "Doenças do aparelho respiratório", "EMG"),
        ("R10.4", "Dor abdominal", "Sintomas e sinais", "EMG"),
        ("S93.4", "Entorse do tornozelo", "Lesões e traumatismos", "EMG"),
        ("I10", "Hipertensão essencial", "Doenças do aparelho circulatório", "EMG"),
        ("E11.9", "Diabetes mellitus tipo 2", "Doenças endócrinas", "CLI"),
        ("J18.9", "Pneumonia não especificada", "Doenças do aparelho respiratório", "CLI"),
        ("N39.0", "Infecção do trato urinário", "Doenças do aparelho geniturinário", "CLI"),
        ("M17.1", "Gonartrose primária", "Doenças do sistema osteomuscular", "ORT"),
        ("S83.2", "Ruptura de menisco", "Lesões e traumatismos", "ORT"),
        ("M51.1", "Transtorno de disco lombar", "Doenças do sistema osteomuscular", "ORT"),
        ("I21.9", "Infarto agudo do miocárdio", "Doenças do aparelho circulatório", "CAR"),
        ("I25.1", "Doença aterosclerótica do coração", "Doenças do aparelho circulatório", "CAR"),
        ("I48", "Fibrilação atrial", "Doenças do aparelho circulatório", "CAR"),
        ("K80.2", "Colelitíase", "Doenças do aparelho digestivo", "CIR"),
        ("K40.9", "Hérnia inguinal", "Doenças do aparelho digestivo", "CIR"),
        ("N80.0", "Endometriose do útero", "Doenças do aparelho geniturinário", "GIN"),
        ("D25.9", "Leiomioma do útero", "Neoplasias benignas", "GIN"),
        ("G40.9", "Epilepsia", "Doenças do sistema nervoso", "NEU"),
        ("I63.9", "Acidente vascular cerebral isquêmico", "Doenças do aparelho circulatório", "NEU"),
        ("C50.9", "Neoplasia maligna da mama", "Neoplasias malignas", "ONC"),
        ("C34.9", "Neoplasia maligna do pulmão", "Neoplasias malignas", "ONC"),
        ("C18.9", "Neoplasia maligna do cólon", "Neoplasias malignas", "ONC")]
CID_POR_ESP = defaultdict(list)
for c in CIDS:
    CID_POR_ESP[c[3]].append(c[0])
MOTIVOS_GLOSA = [("1801", "Procedimento realizado sem autorização prévia", "AUTORIZACAO"),
                 ("1705", "Valor cobrado acima do preço contratado", "PRECO"),
                 ("1909", "Acomodação cobrada incompatível com o plano", "ELEGIBILIDADE"),
                 ("1301", "Beneficiário fora da vigência", "ELEGIBILIDADE"),
                 ("1602", "Falta de justificativa técnica", "TECNICA"),
                 ("2001", "Cobrança em duplicidade", "ADMINISTRATIVA"),
                 ("2010", "Documentação incompleta", "ADMINISTRATIVA")]
CANAIS = [("TEL", "Telefone"), ("WHATSAPP", "WhatsApp"), ("CHAT", "Chat no site"), ("EMAIL", "E-mail"),
          ("PRESENCIAL", "Presencial")]
ASSUNTOS = [("AUT01", "Status de autorização", "AUTORIZACAO"), ("AUT02", "Negativa de autorização", "AUTORIZACAO"),
            ("FAT01", "Cobrança indevida ao paciente", "FATURAMENTO"), ("FAT02", "Segunda via e dúvidas sobre conta", "FATURAMENTO"),
            ("AGD01", "Agendamento de consulta", "AGENDAMENTO"), ("AGD02", "Agendamento de exame", "AGENDAMENTO"),
            ("RES01", "Resultado de exame", "RESULTADO"), ("OUV01", "Reclamação na ouvidoria", "OUVIDORIA")]

NOMES_F = "Ana Beatriz Camila Daniela Eduarda Fernanda Gabriela Helena Isabela Juliana Larissa Mariana Natália Patrícia Renata Sofia Tatiana Vanessa Aline Bruna Carla Débora Elaine Flávia Giovana Luana Marina Paula Raquel Simone".split()
NOMES_M = "André Bruno Carlos Daniel Eduardo Felipe Gabriel Henrique Igor João Lucas Marcelo Nicolas Otávio Paulo Rafael Sérgio Thiago Vinícius Wagner Alexandre Caio Diego Fábio Gustavo Leonardo Mateus Pedro Rodrigo Victor".split()
SOBRENOMES = "Silva Santos Oliveira Souza Rodrigues Ferreira Alves Pereira Lima Gomes Costa Ribeiro Martins Carvalho Almeida Lopes Soares Fernandes Vieira Barbosa Rocha Dias Nascimento Andrade Moreira Nunes Marques Machado Mendes Freitas Cardoso Ramos Teixeira Correia Moura Campos Prado Menezes Azevedo Cavalcanti".split()
CIDADES = {"SP": ["São Paulo", "Guarulhos", "Osasco", "Santo André", "São Bernardo do Campo"],
           "PR": ["Curitiba", "São José dos Pinhais", "Colombo", "Araucária"]}


def nome(sexo):
    return f"{R.choice(NOMES_F if sexo == 'F' else NOMES_M)} {R.choice(SOBRENOMES)} {R.choice(SOBRENOMES)}"


def cpf():
    d = [R.randint(0, 9) for _ in range(9)]
    for n in (10, 11):
        s = sum(v * (n - i) for i, v in enumerate(d)) * 10 % 11
        d.append(0 if s == 10 else s)
    return "".join(map(str, d))


def dia_aleatorio(a, b):
    return a + dt.timedelta(days=R.randint(0, (b - a).days))


# ------------------------------------------------------------------ médicos
MEDICOS, mid = [], 1001
ESTRUTURA = {"U01": {"EMG": 6, "CLI": 6, "CIR": 5, "ORT": 4, "CAR": 4, "GIN": 3, "NEU": 2},
             "U02": {"EMG": 4, "CLI": 4, "CIR": 3, "ORT": 3, "CAR": 2},
             "U03": {"ONC": 8, "CLI": 1}, "U04": {"CLI": 3, "ORT": 1, "GIN": 1, "CAR": 1}}
POR_UNI_ESP = defaultdict(list)
crms = set()
for u, esps in ESTRUTURA.items():
    uf = "PR" if u == "U02" else "SP"
    for e, n in esps.items():
        for _ in range(n):
            if u == "U02" and e == "ORT" and not any(m[1] == "Ricardo Menezes Prado" for m in MEDICOS):
                nm, sx = "Ricardo Menezes Prado", "M"
            else:
                sx = R.choice("FM")
                nm = nome(sx)
            while (c := str(R.randint(40000, 199999))) in crms:
                pass
            crms.add(c)
            MEDICOS.append((mid, nm, c, uf, e, u))
            POR_UNI_ESP[(u, e)].append(mid)
            mid += 1
RICARDO = next(m[0] for m in MEDICOS if m[1] == "Ricardo Menezes Prado")

# ------------------------------------------------------------------ preços contratados
PRECOS = []  # (op, proc, ini, fim, valor)
for op in FATOR_OP:
    for p in PROCEDIMENTOS:
        v = round(p[4] * FATOR_OP[op], 2)
        if op == "OP01":  # reajuste contratual da Alfa em jul/2026
            PRECOS += [(op, p[0], dt.date(2025, 1, 1), dt.date(2026, 6, 30), v),
                       (op, p[0], dt.date(2026, 7, 1), None, round(v * 1.06, 2))]
        else:
            PRECOS.append((op, p[0], dt.date(2025, 1, 1), None, v))


def preco(op, proc, d):
    return next(v for o, p, i, f, v in PRECOS if o == op and p == proc and i <= d and (f is None or d <= f))


# ------------------------------------------------------------------ pacientes e beneficiários
PACIENTES, BENEF, VINCULOS = [], [], defaultdict(list)
cpfs, bid, cart = set(), 500001, set()
planos_ids = [p[0] for p in PLANOS]
pesos_planos = [PESO_PLANO[p] for p in planos_ids]
PLANO = {p[0]: p for p in PLANOS}
for pid in range(1, 4001):
    sx = R.choice("FM")
    while (c := cpf()) in cpfs:
        pass
    cpfs.add(c)
    uf = "PR" if R.random() < .25 else "SP"
    nasc = dt.date(1940, 1, 1) + dt.timedelta(days=R.randint(0, 365 * 66))
    PACIENTES.append((pid, nome(sx), c, nasc, sx, R.choice(CIDADES[uf]), uf))
    plano = R.choices(planos_ids, pesos_planos)[0]
    ini = dia_aleatorio(dt.date(2019, 1, 1), dt.date(2025, 9, 30))
    trocas = R.random() < .08
    fim = dt.date(2026, 3, 31) if trocas else None
    for k in range(2 if trocas else 1):
        if k == 1:
            plano = R.choice([p for p in planos_ids if p != plano])
            ini, fim = dt.date(2026, 4, 1), None
        while (n := f"{PLANO[plano][1][2:]}{R.randint(10**13, 10**14 - 1)}") in cart:
            pass
        cart.add(n)
        BENEF.append((bid, pid, plano, n, ini, fim))
        VINCULOS[pid].append((bid, plano, ini, fim))
        bid += 1


def vinculo(pid, d):
    return next(v for v in VINCULOS[pid] if v[2] <= d and (v[3] is None or d <= v[3]))


onc_pacientes = R.sample(range(1, 4001), 260)
pac_geral = [p for p in range(1, 4001) if p not in set(onc_pacientes)]
peso_pac = [R.paretovariate(1.6) for _ in pac_geral]

# ------------------------------------------------------------------ atendimentos, autorizações, contas
AUT, ATD, CONTAS, ITENS, GLOSAS, RECURSOS, PAGTOS = [], [], [], [], [], [], []
aut_id, atd_id, item_id, glosa_id = 2025000001, 1, 1, 1
OPERADORA_DO_PLANO = {p[0]: p[1] for p in PLANOS}
PRAZO = {o[0]: o[3] for o in OPERADORAS}
historias = defaultdict(int)


def medico(u, esp):
    lista = POR_UNI_ESP[(u, esp)] or POR_UNI_ESP[(u, "CLI")]
    if u == "U02" and esp == "ORT" and R.random() < .5:
        return RICARDO
    return R.choice(lista)


def itens_do_atendimento(tipo, esp, dias, plano, u, d):
    """Lista de (procedimento, quantidade, executante?) do atendimento."""
    it = []
    if tipo == "PS":
        it += [("10101039", 1, True), ("60000102", 1, False)]
        it += [("90000101", 1, False)] if R.random() < .7 else []
        it += [("40304361", 1, False)] if R.random() < .5 else []
        it += [("40901114", 1, False)] if R.random() < .3 else []
        it += [("41001010", 1, False)] if R.random() < .12 else []
        it += [("85000102", 1, False)] if R.random() < .3 else []
    elif tipo == "AMBULATORIAL":
        it.append(("10101012", 1, True))
        extra = {"ORT": [("41101014", .45)], "CAR": [("40801020", .6)], "CLI": [("40304361", .6), ("40901300", .25)],
                 "GIN": [("40901300", .5)]}.get(esp, [])
        it += [(p, 1, False) for p, pr in extra if R.random() < pr]
    elif tipo == "ONCOLOGIA":
        it += [("20104219", 1, True), ("90000103", 1, False), ("85000103", 1, False), ("40304361", 1, False)]
        it += [("10101012", 1, True)] if R.random() < .3 else []
    else:  # INTERNACAO
        cir = {"ORT": [(("30725046", "70000303"), .5), (("30724040", "70000101"), .5)],
               "CAR": [(("30912016", "70000202"), .6)], "CIR": [(("31005497",), .6), (("31009166",), .4)],
               "GIN": [(("31303080",), 1.0)]}.get(esp, [])
        r, acum, escolhido = R.random(), 0, None
        for procs, pr in cir:
            acum += pr
            if r < acum:
                escolhido = procs
                break
        if escolhido:
            it += [(escolhido[0], 1, True), ("60000101", 1, False), ("85000101", 1, False)]
            it += [(p, 1, False) for p in escolhido[1:]]
        acomod = PLANO[plano][4]
        diaria = "80000102" if acomod == "APARTAMENTO" else "80000101"
        if acomod == "ENFERMARIA":
            upgrade = .40 if (plano == "DEL-ESS" and u == "U01") else .03     # O3
            if R.random() < upgrade:
                diaria = "80000102"
        uti = 0
        if (escolhido and escolhido[0] == "30912016" and R.random() < .5) or (esp == "NEU" and R.random() < .3):
            uti = R.randint(1, 2)
        if dias - uti > 0:
            it.append((diaria, dias - uti, False))
        if uti:
            it.append(("80000103", uti, False))
        it += [("60000103", dias, False), ("90000104", dias, False), ("40304361", max(1, math.ceil(dias / 2)), False)]
        it += [("40901114", 1, False)] if R.random() < .5 else []
        it += [("90000102", dias * 2, False)] if esp in ("CLI", "NEU") or R.random() < .3 else []
    return it


TAXA_DIA = {"PS": 11, "AMBULATORIAL": 8, "INTERNACAO": 6, "ONCOLOGIA": 2.5}
UNI_TIPO = {"PS": (["U01", "U02"], [.6, .4]), "AMBULATORIAL": (["U04", "U01", "U02"], [.5, .3, .2]),
            "INTERNACAO": (["U01", "U02"], [.65, .35]), "ONCOLOGIA": (["U03"], [1.0])}
ESP_TIPO = {"PS": (["EMG"], [1]), "AMBULATORIAL": (["CLI", "ORT", "GIN", "CAR"], [.4, .3, .15, .15]),
            "INTERNACAO": (["CIR", "ORT", "CAR", "CLI", "NEU", "GIN"], [.22, .22, .18, .22, .08, .08]),
            "ONCOLOGIA": (["ONC"], [1])}
ITENS_POR_CONTA = defaultdict(list)
atendimentos_meta = {}

d = INICIO
while d <= HOJE:
    fator = .55 if d.weekday() == 6 else .75 if d.weekday() == 5 else 1.0
    for tipo, taxa in TAXA_DIA.items():
        if tipo in ("AMBULATORIAL", "ONCOLOGIA", "INTERNACAO") and d.weekday() == 6:
            continue
        lam = taxa * (fator if tipo == "PS" else 1)
        for _ in range(sum(1 for _ in range(int(lam * 3)) if R.random() < 1 / 3)):
            unis, pu = UNI_TIPO[tipo]
            esps, pe = ESP_TIPO[tipo]
            u = R.choices(unis, pu)[0]
            esp = R.choices(esps, pe)[0]
            if u == "U04" and esp not in ("CLI", "ORT", "GIN", "CAR"):
                esp = "CLI"
            if not POR_UNI_ESP[(u, esp)]:
                u = "U01"
            pid = R.choice(onc_pacientes) if tipo == "ONCOLOGIA" else R.choices(pac_geral, peso_pac)[0]
            ben, plano, *_ = vinculo(pid, d)
            op = OPERADORA_DO_PLANO[plano]
            med = medico(u, esp)
            dias = {"PS": 0, "AMBULATORIAL": 0, "ONCOLOGIA": 0}.get(tipo) if tipo != "INTERNACAO" else (
                R.randint(1, 3) if esp in ("CIR", "GIN") else R.randint(2, 4) if esp == "ORT" else R.randint(3, 8))
            itens = itens_do_atendimento(tipo, esp, dias, plano, u, d)
            # autorização prévia
            exige = [p for p, _, _ in itens if PROC[p][3]]
            guia, negada = None, False
            if exige:
                principal = exige[0]
                antec = R.randint(1, 3) if tipo == "ONCOLOGIA" else R.randint(2, 10)
                sol = dt.datetime.combine(d - dt.timedelta(days=antec), dt.time(R.randint(8, 18), R.randint(0, 59)))
                resp = sol + dt.timedelta(hours=R.randint(4, 72))
                p_neg = .03
                if op == "OP02" and d >= dt.date(2026, 5, 1) and principal in ("41101014", "30725046", "30724040"):
                    p_neg = .35                                                                   # O1
                negada = R.random() < p_neg
                motivo = None
                if negada:
                    motivo = R.choice(["Indicação clínica não comprovada", "Necessita de segunda opinião médica",
                                       "Procedimento fora da cobertura contratual"])
                guia = aut_id
                AUT.append([aut_id, ben, med, u, principal, sol, resp, "NEGADA" if negada else "APROVADA", motivo])
                aut_id += 1
                if negada:
                    historias["guias_negadas"] += 1
                    if R.random() < .55:          # paciente desiste: só fica a guia negada
                        continue
                    historias["atendidos_com_guia_negada"] += 1
            entrada = dt.datetime.combine(d, dt.time(R.randint(0, 23) if tipo == "PS" else R.randint(7, 17), R.randint(0, 59)))
            alta = entrada + (dt.timedelta(hours=R.randint(2, 8)) if tipo == "PS" else dt.timedelta(hours=R.randint(1, 4))
                              if dias == 0 else dt.timedelta(days=dias, hours=R.randint(-3, 5)))
            alta = alta if alta <= AGORA else None
            ATD.append((atd_id, pid, ben, u, med, guia, R.choice(CID_POR_ESP[esp]), tipo, entrada, alta))
            atendimentos_meta[atd_id] = (pid, op, plano, u, med, tipo, entrada.date(), negada, guia, itens)
            atd_id += 1
    d += dt.timedelta(days=1)

# guias pendentes (pedidas nos últimos dias, sem resposta)
for _ in range(45):
    pid = R.choice(pac_geral)
    ben, plano, *_ = vinculo(pid, HOJE)
    sol = dt.datetime.combine(dia_aleatorio(HOJE - dt.timedelta(days=4), HOJE), dt.time(R.randint(8, 18), R.randint(0, 59)))
    sol = min(sol, AGORA - dt.timedelta(hours=1))
    AUT.append([aut_id, ben, R.choice(POR_UNI_ESP[("U01", "ORT")] + POR_UNI_ESP[("U02", "ORT")]), R.choice(["U01", "U02"]),
                R.choice(["41101014", "30725046", "30724040"]), sol, None, "PENDENTE", None])
    aut_id += 1

conta_id = 9000001
for aid, (pid, op, plano, u, med, tipo, d0, negada, guia, itens) in atendimentos_meta.items():
    alta = ATD[aid - 1][9]
    if alta is None or alta.date() + dt.timedelta(days=3) > HOJE:
        continue
    fech = alta.date() + dt.timedelta(days=3)
    envio = fech + dt.timedelta(days=R.randint(1, 4))
    envio = envio if envio <= HOJE else None
    analise = envio + dt.timedelta(days=25) if envio else None
    pagto = envio + dt.timedelta(days=PRAZO[op]) if envio else None
    total, glosado, tem_glosa = 0.0, 0.0, False
    for p, q, exe in itens:
        dex = d0
        vu = preco(op, p, dex)
        if med == RICARDO and PROC[p][2] == "OPME" and dex >= dt.date(2026, 2, 1):
            vu = round(vu * 1.25, 2)                                                              # O2
        vt = round(vu * q, 2)
        ITENS.append((item_id, conta_id, p, med if exe else None, dex, q, vu, vt))
        total += vt
        # glosas: só depois da análise da operadora
        if analise and analise <= HOJE:
            g = None
            if negada and PROC[p][3] and R.random() < .9:
                g = ("1801", vt)
            elif med == RICARDO and PROC[p][2] == "OPME" and dex >= dt.date(2026, 2, 1) and R.random() < .85:
                g = ("1705", round(vt - preco(op, p, dex) * q, 2))
            elif p == "80000102" and PLANO[plano][4] == "ENFERMARIA" and R.random() < .95:
                g = ("1909", round((vu - preco(op, "80000101", dex)) * q, 2))
            elif R.random() < .015:
                m = R.choice(["1602", "2010", "2001", "1301"])
                g = (m, vt if m == "2001" else round(vt * R.uniform(.3, 1), 2))
            if g and g[1] > 0:
                dg = analise - dt.timedelta(days=R.randint(0, 5))
                GLOSAS.append((glosa_id, item_id, g[0], dg, g[1]))
                glosado += g[1]
                tem_glosa = True
                glosa_id += 1
        item_id += 1
    status = "ABERTA" if not envio else "GLOSADA_PARCIAL" if tem_glosa else (
        "PAGA" if pagto <= HOJE else "ENVIADA")
    CONTAS.append((conta_id, aid, op, fech, envio, round(total, 2), status))
    if pagto and pagto <= HOJE:
        PAGTOS.append((len(PAGTOS) + 1, conta_id, pagto, round(total - glosado, 2)))
    atendimentos_meta[aid] = atendimentos_meta[aid] + (conta_id,)
    conta_id += 1

ACEITE = {"1801": .35, "1705": .20, "1909": .10}
for gid, iid, mot, dg, v in GLOSAS:
    if dg + dt.timedelta(days=10) > HOJE or R.random() > .6:
        continue
    dr = dg + dt.timedelta(days=R.randint(5, 15))
    if dr + dt.timedelta(days=30) > HOJE:
        st, rec = "EM_ANALISE", 0
    else:
        ok = R.random() < ACEITE.get(mot, .5)
        st, rec = ("ACEITO", v) if ok else ("NEGADO", 0)
    RECURSOS.append((len(RECURSOS) + 1, gid, min(dr, HOJE), st, rec))

# ------------------------------------------------------------------ central: protocolos e pesquisas
PROT, PESQ = [], []
item_conta = {i[0]: i[1] for i in ITENS}
conta_atd = {c[0]: c[1] for c in CONTAS}


def canal(quando):
    meses = (quando.year - INICIO.year) * 12 + quando.month - INICIO.month
    zap = .20 + .02 * meses
    return R.choices(["TEL", "WHATSAPP", "CHAT", "EMAIL", "PRESENCIAL"], [.82 - zap, zap, .10, .05, .03])[0]


def protocolo(pid, assunto, quando, aut=None, atd=None, conta=None, fcr=.78):
    if quando > AGORA:
        return
    resolvido = R.random() < fcr
    dur = dt.timedelta(minutes=R.randint(5, 40)) if resolvido else dt.timedelta(days=R.randint(1, 6))
    fecha = quando + dur
    if fecha > AGORA:
        st, fecha = "ABERTO", None
    else:
        st = "RESOLVIDO" if resolvido or R.random() < .8 else "ESCALADO"
    PROT.append([len(PROT) + 1, pid, canal(quando.date()), assunto, aut, atd, conta, quando, fecha, st, int(resolvido)])


def instante(d, h0=7, h1=21):
    return dt.datetime.combine(d, dt.time(R.randint(h0, h1), R.randint(0, 59), R.randint(0, 59)))


ben_pac = {b[0]: b[1] for b in BENEF}
for a in AUT:
    pid = ben_pac[a[1]]
    if R.random() < .30:
        protocolo(pid, "AUT01", a[5] + dt.timedelta(hours=R.randint(2, 48)), aut=a[0], fcr=.85)
    if a[7] == "NEGADA" and R.random() < .8:
        q = a[6] + dt.timedelta(hours=R.randint(1, 30))
        protocolo(pid, "AUT02", q, aut=a[0], fcr=.35)
        if R.random() < .3:
            protocolo(pid, "OUV01", q + dt.timedelta(days=R.randint(2, 6)), aut=a[0], fcr=.2)
glosa_item = {}
for gid, iid, mot, dg, v in GLOSAS:
    glosa_item.setdefault(item_conta[iid], []).append((mot, dg))
for c, gl in glosa_item.items():
    for mot, dg in gl:
        if mot == "1909" and R.random() < .85:
            protocolo(atendimentos_meta[conta_atd[c]][0], "FAT01",
                      instante(dg + dt.timedelta(days=R.randint(5, 20))), conta=c, fcr=.45)
            break
for aid, meta in atendimentos_meta.items():
    if meta[5] in ("PS", "AMBULATORIAL") and R.random() < .15:
        protocolo(meta[0], "RES01", instante(meta[6] + dt.timedelta(days=R.randint(1, 5))), atd=aid, fcr=.9)
for c in R.sample(CONTAS, 700):
    if c[4]:
        protocolo(atendimentos_meta[c[1]][0], "FAT02", instante(c[4] + dt.timedelta(days=R.randint(1, 40))), conta=c[0])
    if R.random() < .02:
        protocolo(atendimentos_meta[c[1]][0], "FAT01", instante(c[3] + dt.timedelta(days=R.randint(1, 30))), conta=c[0], fcr=.6)
for _ in range(6500):
    protocolo(R.randint(1, 4000), R.choices(["AGD01", "AGD02"], [.6, .4])[0], instante(dia_aleatorio(INICIO, HOJE)), fcr=.82)
PROT.sort(key=lambda p: p[7])
for i, p in enumerate(PROT, 1):
    p[0] = i
MEDIA_CSAT = {"AUT02": 2.3, "OUV01": 1.8, "FAT01": 2.7, "AUT01": 3.9}
for p in PROT:
    if p[9] == "RESOLVIDO" and R.random() < .25:
        cs = MEDIA_CSAT.get(p[3], 4.4) - (0 if p[10] else .6) + R.gauss(0, .7)
        cs = max(1, min(5, round(cs)))
        resp = p[8] + dt.timedelta(minutes=R.randint(10, 600))
        if resp <= AGORA:
            PESQ.append((len(PESQ) + 1, p[0], resp, cs, max(0, min(10, cs * 2 - 1 + R.randint(-1, 1)))))


# ------------------------------------------------------------------ SQL
def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, dt.datetime):
        return f"'{v:%Y-%m-%d %H:%M:%S}'"
    if isinstance(v, dt.date):
        return f"'{v:%Y-%m-%d}'"
    return "N'" + str(v).replace("'", "''") + "'"


TABELAS = [
    ("cadastro.unidades", "unidade_id, nome, tipo, cidade, uf, leitos", UNIDADES),
    ("cadastro.especialidades", "especialidade_id, nome", ESPECIALIDADES),
    ("cadastro.medicos", "medico_id, nome, crm, uf_crm, especialidade_id, unidade_id", MEDICOS),
    ("cadastro.operadoras", "operadora_id, nome, registro_ans, prazo_pagamento_dias", OPERADORAS),
    ("cadastro.planos", "plano_id, operadora_id, nome, segmentacao, acomodacao", PLANOS),
    ("cadastro.pacientes", "paciente_id, nome, cpf, data_nascimento, sexo, cidade, uf", PACIENTES),
    ("cadastro.beneficiarios", "beneficiario_id, paciente_id, plano_id, numero_carteirinha, vigencia_inicio, vigencia_fim", BENEF),
    ("cadastro.procedimentos", "procedimento_id, descricao, grupo, exige_autorizacao", [p[:4] for p in PROCEDIMENTOS]),
    ("cadastro.precos_contratados", "operadora_id, procedimento_id, vigencia_inicio, vigencia_fim, valor", PRECOS),
    ("cadastro.cids", "cid, descricao, capitulo", [c[:3] for c in CIDS]),
    ("assistencial.autorizacoes", "autorizacao_id, beneficiario_id, medico_solicitante_id, unidade_id, procedimento_id, "
                                  "data_solicitacao, data_resposta, status, motivo_negativa", AUT),
    ("assistencial.atendimentos", "atendimento_id, paciente_id, beneficiario_id, unidade_id, medico_responsavel_id, "
                                  "autorizacao_id, cid_principal, tipo, data_entrada, data_alta", ATD),
    ("faturamento.contas", "conta_id, atendimento_id, operadora_id, data_fechamento, data_envio, valor_total, status", CONTAS),
    ("faturamento.itens_conta", "item_id, conta_id, procedimento_id, medico_executante_id, data_execucao, quantidade, "
                                "valor_unitario, valor_total", ITENS),
    ("faturamento.motivos_glosa", "motivo_glosa_id, descricao, categoria", MOTIVOS_GLOSA),
    ("faturamento.glosas", "glosa_id, item_id, motivo_glosa_id, data_glosa, valor_glosado", GLOSAS),
    ("faturamento.recursos_glosa", "recurso_id, glosa_id, data_recurso, status, valor_recuperado", RECURSOS),
    ("faturamento.pagamentos", "pagamento_id, conta_id, data_pagamento, valor_pago", PAGTOS),
    ("relacionamento.canais", "canal_id, nome", CANAIS),
    ("relacionamento.assuntos", "assunto_id, nome, area", ASSUNTOS),
    ("relacionamento.protocolos", "protocolo_id, paciente_id, canal_id, assunto_id, autorizacao_id, atendimento_id, conta_id, "
                                  "data_abertura, data_fechamento, status, resolvido_primeiro_contato", PROT),
    ("relacionamento.pesquisas_satisfacao", "pesquisa_id, protocolo_id, data_resposta, csat, nps", PESQ)]

with SAIDA.open("w", encoding="utf-8") as f:
    f.write("/* Gerado por gerar_dados.py (seed 42). Não editar à mão. */\nSET NOCOUNT ON;\nGO\n")
    for tabela, cols, linhas in TABELAS:
        for i in range(0, len(linhas), 1000):
            vals = ",\n".join("(" + ", ".join(lit(v) for v in row) + ")" for row in linhas[i:i + 1000])
            f.write(f"SET NOCOUNT ON;\nINSERT INTO {tabela} ({cols}) VALUES\n{vals};\nGO\n")
import os
if os.environ.get("CSV_DIR"):              # só para testes: as mesmas linhas em CSV (uma pasta por tabela)
    import csv
    for tabela, cols, linhas in TABELAS:
        pasta = Path(os.environ["CSV_DIR"]) / tabela.split(".")[1]
        pasta.mkdir(parents=True, exist_ok=True)
        with (pasta / "part-0.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([c.strip() for c in cols.split(",")] + ["atualizado_em"])
            for row in linhas:
                w.writerow(["" if v is None else int(v) if isinstance(v, bool) else
                            f"{v:%Y-%m-%d %H:%M:%S}" if isinstance(v, dt.datetime) else v for v in row] + ["2026-10-26 12:00:00"])
for tabela, _, linhas in TABELAS:
    print(f"{tabela:40s} {len(linhas):>7,}")
print(dict(historias), f"→ {SAIDA.name} ({SAIDA.stat().st_size / 1e6:.1f} MB)")
