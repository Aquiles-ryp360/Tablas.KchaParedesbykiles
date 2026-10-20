"""Ejercicio 230 °C, 230 kg/s. Ejecutar desde cualquier directorio, Python 3.11+."""
from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from thermo_solver.database import ThermoDatabase
from thermo_solver.r600a import R600aTables


def calculate():
    water = ThermoDatabase(); iso = R600aTables()
    a, c = water.saturation_by_pressure(5), water.saturation_by_pressure(.1)
    with water.connect() as connection:
        feed = water._sat_from_row(connection.execute('SELECT * FROM saturated_water WHERE CAST(T_C AS REAL)=230 LIMIT 1').fetchone())
    seven = water.pt(5,90)
    eight, nine, ten = iso.pt(32.5,145), iso.pt(4,80), iso.saturation(4)
    m = 230.; eta_pump=.9; h0=104.83
    x2=(feed.h_f-a.h_f)/a.h_fg
    ms=m*x2; mb=m-ms
    h4=c.h_f+.9*c.h_fg
    wp=ten['v_f_m3kg']*(3250-400)/eta_pump
    h11=ten['h_f_kJkg']+wp
    qhx=mb*(a.h_f-seven.h_kJkg)
    mi=qhx/(eight['h_kJkg']-h11)
    wflash=ms*(a.h_g-h4)
    wt=mi*(eight['h_kJkg']-nine['h_kJkg']); wbp=mi*wp
    wbin=wt-wbp; wtotal=wflash+wbin
    qcflash=ms*(h4-c.h_f); qciso=mi*(nine['h_kJkg']-ten['h_f_kJkg'])
    qflash=ms*(a.h_g-c.h_f); qret=qflash+qhx
    qresource=m*(feed.h_f-h0)
    assert abs(qhx-wbin-qciso)<1e-7
    assert abs(qret-wtotal-qcflash-qciso)<1e-7
    states=[dict(state='1',fluid='Agua',P=feed.P_bar,T=230,h=feed.h_f,s=feed.s_f,flow=m),dict(state='2',fluid='Agua',P=5,T=a.T_C,h=feed.h_f,s=a.s_f+x2*a.s_fg,flow=m),dict(state='3',fluid='Agua',P=5,T=a.T_C,h=a.h_g,s=a.s_g,flow=ms),dict(state='4',fluid='Agua',P=.1,T=c.T_C,h=h4,s=c.s_f+.9*c.s_fg,flow=ms),dict(state='5',fluid='Agua',P=.1,T=c.T_C,h=c.h_f,s=c.s_f,flow=ms),dict(state='6',fluid='Agua',P=5,T=a.T_C,h=a.h_f,s=a.s_f,flow=mb),dict(state='7',fluid='Agua',P=5,T=90,h=seven.h_kJkg,s=seven.s_kJkgK,flow=mb)]
    for label,point in [('8',eight),('9',nine)]:states.append(dict(state=label,fluid='Isobutano',P=point['P_bar'],T=point['T_C'],h=point['h_kJkg'],s=point['s_kJkgK'],flow=mi))
    states += [dict(state='10',fluid='Isobutano',P=4,T=ten['T_bubble_C'],h=ten['h_f_kJkg'],s=ten['s_f_kJkgK'],flow=mi),dict(state='11',fluid='Isobutano',P=32.5,T=None,h=h11,s=None,flow=mi)]
    return dict(states=states,eight=eight,nine=nine,ten=ten,h11=h11,x2=x2,ms=ms,mb=mb,miso=mi,wp=wp,Qhx=qhx,Wflash=wflash,Wtiso=wt,Wp=wbp,Wbin=wbin,Wtotal=wtotal,QCflash=qcflash,QCiso=qciso,Qflash=qflash,Qin=qret,Qgeo=m*feed.h_f-ms*c.h_f-mb*seven.h_kJkg,Qresource=qresource,effbin=wbin/qhx,effcomb=wtotal/qret,effresource=wtotal/qresource,eff20=wtotal/(m*(feed.h_f-83.84)),assumptions=dict(ambient_C=25,h0_kJkg=h0,pump_model='Líquido incompresible: w=vΔP/eta',pump_efficiency=.9,auxiliary_loads='No especificados; se incluye la bomba de isobutano',state11_T_s='No determinados por estas tablas de saturación y vapor'))


if __name__ == '__main__':
    result=calculate()
    path=ROOT/'examples'/'flash_binario_230C'/'results.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k]for k in ['miso','Wflash','Wbin','Wtotal','effbin','effresource']},indent=2))
