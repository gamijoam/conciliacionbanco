import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame} from 'remotion';
import {AVISO_LEGAL, C, ESLOGAN, WHATSAPP} from './config';
import {Fondo, Marca, Sube, TarjetaApp, useEntrada, useSalida} from './componentes';
import {Candado, Chat, Check, Lista, Logo, Personas, Reloj} from './iconos';

export const ESCENAS = {gancho: 95, dolor: 140, revelacion: 80, demo: 225, fraude: 130, beneficios: 135, cierre: 120};
export const DURACION_VIDEO = Object.values(ESCENAS).reduce((a, b) => a + b, 0);

const escribir = (texto: string, frame: number, desde: number, hasta: number) =>
	texto.slice(0, Math.round(interpolate(frame, [desde, hasta], [0, texto.length], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})));

const Titulo: React.FC<{children: React.ReactNode; size?: number; color?: string}> = ({children, size = 84, color}) => (
	<div style={{fontSize: size, fontWeight: 800, lineHeight: 1.08, letterSpacing: -size * 0.025, textAlign: 'center', color, textWrap: 'balance'} as React.CSSProperties}>{children}</div>
);

// 1 · Gancho: llega una captura de pago
const Gancho: React.FC = () => {
	const frame = useCurrentFrame();
	const salida = useSalida(ESCENAS.gancho);
	const burbuja = useEntrada(18);
	const adjunto = useEntrada(32);
	const duda = useEntrada(58);
	return (
		<Fondo>
			<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 70, opacity: salida, padding: 80}}>
				<Sube>
					<Titulo size={104}>
						¿Te llegó el
						<br />
						<span style={{color: C.marca}}>pago móvil?</span>
					</Titulo>
				</Sube>
				<div style={{width: 820, display: 'flex', flexDirection: 'column', gap: 18}}>
					<div
						style={{
							alignSelf: 'flex-start',
							background: C.blanco,
							borderRadius: '30px 30px 30px 8px',
							padding: '26px 34px',
							fontSize: 40,
							fontWeight: 500,
							boxShadow: '0 12px 30px rgba(11,31,58,.12)',
							opacity: burbuja,
							transform: `translateX(${(1 - burbuja) * -60}px)`,
						}}
					>
						Listo, ya te pagué
					</div>
					<div
						style={{
							alignSelf: 'flex-start',
							width: 560,
							background: C.blanco,
							borderRadius: '30px 30px 30px 8px',
							padding: 22,
							boxShadow: '0 12px 30px rgba(11,31,58,.12)',
							opacity: adjunto,
							transform: `translateX(${(1 - adjunto) * -60}px)`,
						}}
					>
						<div style={{background: '#EEF2F8', borderRadius: 18, padding: '26px 28px'}}>
							<div style={{fontSize: 24, color: C.tintaSuave, fontWeight: 600}}>Comprobante de pago</div>
							<div style={{fontSize: 52, fontWeight: 800, marginTop: 8}}>Bs. 2.000,00</div>
							<div style={{fontSize: 26, color: C.tintaSuave, marginTop: 6}}>Ref. 0001 2312 3456</div>
						</div>
					</div>
				</div>
				<div style={{opacity: duda, transform: `scale(${0.8 + duda * 0.2}) rotate(${Math.sin(frame / 6) * 2}deg)`, fontSize: 64, fontWeight: 800, color: C.rojo}}>
					¿Será verdad?
				</div>
			</AbsoluteFill>
		</Fondo>
	);
};

// 2 · Dolor: todo lo que hay que hacer para comprobarlo
const PASOS = ['Abrir el banco', 'Usuario, clave y código', 'Buscar entre cientos de movimientos', 'Revisar referencia y monto'];
const Dolor: React.FC = () => {
	const frame = useCurrentFrame();
	const salida = useSalida(ESCENAS.dolor);
	const final = useEntrada(95);
	return (
		<Fondo>
			<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 56, opacity: salida, padding: 80}}>
				<Sube>
					<Titulo size={76}>Para saberlo tienes que…</Titulo>
				</Sube>
				<div style={{display: 'flex', flexDirection: 'column', gap: 24, width: 880}}>
					{PASOS.map((p, i) => (
						<Paso key={p} texto={p} n={i + 1} retraso={12 + i * 18} />
					))}
				</div>
				<div style={{display: 'flex', alignItems: 'center', gap: 22, opacity: final, transform: `translateY(${(1 - final) * 30}px)`}}>
					<Reloj size={84} color={C.rojo} angulo={frame * 12} />
					<div style={{fontSize: 54, fontWeight: 800, color: C.rojo}}>…con cada pago.</div>
				</div>
			</AbsoluteFill>
		</Fondo>
	);
};
const Paso: React.FC<{texto: string; n: number; retraso: number}> = ({texto, n, retraso}) => {
	const p = useEntrada(retraso);
	return (
		<div
			style={{
				display: 'flex',
				alignItems: 'center',
				gap: 28,
				background: C.blanco,
				borderRadius: 26,
				padding: '28px 34px',
				boxShadow: '0 10px 26px rgba(11,31,58,.08)',
				opacity: p,
				transform: `translateX(${(1 - p) * 120}px)`,
			}}
		>
			<div style={{width: 64, height: 64, borderRadius: 999, background: C.rojoFondo, color: C.rojo, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 34, fontWeight: 800, flexShrink: 0}}>
				{n}
			</div>
			<div style={{fontSize: 44, fontWeight: 600}}>{texto}</div>
		</div>
	);
};

// 3 · Revelación de la marca
const Revelacion: React.FC = () => {
	const logo = useEntrada(0, 11);
	const salida = useSalida(ESCENAS.revelacion);
	return (
		<Fondo oscuro>
			<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 48, opacity: salida, padding: 90}}>
				<div style={{transform: `scale(${logo}) rotate(${(1 - logo) * -25}deg)`}}>
					<Logo size={240} />
				</div>
				<Sube retraso={10}>
					<Titulo size={120} color={C.blanco}>
						Conciliador
					</Titulo>
				</Sube>
				<Sube retraso={22}>
					<div style={{fontSize: 52, fontWeight: 500, textAlign: 'center', lineHeight: 1.3, opacity: 0.9, textWrap: 'balance'} as React.CSSProperties}>{ESLOGAN}</div>
				</Sube>
			</AbsoluteFill>
		</Fondo>
	);
};

// 4 · Demo: referencia + monto -> Aprobado
const Demo: React.FC = () => {
	const frame = useCurrentFrame();
	const tarjeta = useEntrada(0);
	const resultado = useEntrada(162, 12);
	const salida = useSalida(ESCENAS.demo);
	const ref = escribir('123456', frame, 18, 50);
	const monto = escribir('2.000,00', frame, 62, 98);
	const presion = interpolate(frame, [104, 108, 114], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const estado = frame < 110 ? 'vacio' : frame < 160 ? 'cargando' : 'aprobado';
	const foco = frame < 56 ? 'ref' : frame < 104 ? 'monto' : null;
	const cambio = frame >= 160;
	return (
		<Fondo>
			<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 70, opacity: salida, padding: 80}}>
				<div style={{height: 220, display: 'flex', alignItems: 'center'}}>
					{!cambio ? (
						<Sube key="a">
							<Titulo size={80}>
								Escribe la <span style={{color: C.marca}}>referencia</span>
								<br />y el <span style={{color: C.marca}}>monto</span>
							</Titulo>
						</Sube>
					) : (
						<Sube key="b" retraso={162}>
							<Titulo size={80}>
								Y en segundos sabes
								<br />
								si <span style={{color: C.verde}}>el pago llegó</span>
							</Titulo>
						</Sube>
					)}
				</div>
				<div style={{opacity: tarjeta, transform: `translateY(${(1 - tarjeta) * 80}px) scale(${0.95 + tarjeta * 0.05})`}}>
					<TarjetaApp referencia={ref} monto={monto} foco={foco} estado={estado} botonPresion={presion} resultado={resultado} ancho={920} />
				</div>
			</AbsoluteFill>
		</Fondo>
	);
};

// 5 · Fraude: la misma captura dos veces
const Fraude: React.FC = () => {
	const frame = useCurrentFrame();
	const resultado = useEntrada(52, 12);
	const salida = useSalida(ESCENAS.fraude);
	const estado = frame < 50 ? 'cargando' : 'ya_usada';
	return (
		<Fondo>
			<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 70, opacity: salida, padding: 80}}>
				<div style={{height: 220, display: 'flex', alignItems: 'center'}}>
					{frame < 50 ? (
						<Sube key="a">
							<Titulo size={78}>
								¿Te mandan la <span style={{color: C.ambar}}>misma captura</span> otra vez?
							</Titulo>
						</Sube>
					) : (
						<Sube key="b" retraso={52}>
							<Titulo size={78}>
								Te avisa que <span style={{color: C.ambar}}>ya fue usada</span>
							</Titulo>
						</Sube>
					)}
				</div>
				<TarjetaApp referencia="123456" monto="2.000,00" estado={estado} resultado={resultado} ancho={920} />
			</AbsoluteFill>
		</Fondo>
	);
};

// 6 · Beneficios
const BENEFICIOS = [
	{Icono: Candado, texto: 'Tu clave del banco se queda en tu computadora'},
	{Icono: Personas, texto: 'Tus cajeras verifican desde su PC, cada una con su usuario'},
	{Icono: Lista, texto: 'Historial de cada pago verificado'},
	{Icono: Check, texto: 'Para personas naturales y emprendedores con BDVenlínea'},
];
const Beneficios: React.FC = () => {
	const salida = useSalida(ESCENAS.beneficios);
	return (
		<Fondo>
			<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 56, opacity: salida, padding: 80}}>
				<Sube>
					<Titulo size={84}>Hecho para tu negocio</Titulo>
				</Sube>
				<div style={{display: 'flex', flexDirection: 'column', gap: 26, width: 900}}>
					{BENEFICIOS.map((b, i) => (
						<Beneficio key={b.texto} {...b} retraso={10 + i * 16} />
					))}
				</div>
			</AbsoluteFill>
		</Fondo>
	);
};
const Beneficio: React.FC<{Icono: React.FC<{size?: number; color?: string}>; texto: string; retraso: number}> = ({Icono, texto, retraso}) => {
	const p = useEntrada(retraso);
	return (
		<div style={{display: 'flex', alignItems: 'center', gap: 30, background: C.blanco, borderRadius: 28, padding: '30px 34px', boxShadow: '0 10px 26px rgba(11,31,58,.08)', opacity: p, transform: `translateY(${(1 - p) * 50}px)`}}>
			<div style={{width: 92, height: 92, borderRadius: 24, background: '#E6EEFF', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>
				<Icono size={54} color={C.marca} />
			</div>
			<div style={{fontSize: 42, fontWeight: 600, lineHeight: 1.25}}>{texto}</div>
		</div>
	);
};

// 7 · Cierre con llamado a la acción
export const Cierre: React.FC<{conSalida?: boolean}> = () => {
	const frame = useCurrentFrame();
	const boton = useEntrada(26, 10);
	const latido = 1 + Math.max(0, Math.sin((frame - 40) / 7)) * 0.03 * (frame > 40 ? 1 : 0);
	return (
		<Fondo oscuro>
			<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 64, padding: 80}}>
				<Sube>
					<Titulo size={100} color={C.blanco}>
						Deja de entrar
						<br />
						al banco
						<br />
						<span style={{color: '#7FE0A6'}}>por cada pago</span>
					</Titulo>
				</Sube>
				<div
					style={{
						display: 'flex',
						alignItems: 'center',
						gap: 26,
						background: C.verde,
						borderRadius: 999,
						padding: '34px 56px',
						boxShadow: '0 20px 50px rgba(18,161,80,.45)',
						transform: `scale(${boton * latido})`,
					}}
				>
					<Chat size={70} color={C.blanco} />
					<div>
						<div style={{fontSize: 34, fontWeight: 600, opacity: 0.9}}>Escríbenos por WhatsApp</div>
						<div style={{fontSize: 56, fontWeight: 800, fontVariantNumeric: 'tabular-nums'}}>{WHATSAPP}</div>
					</div>
				</div>
				<Sube retraso={40}>
					<Marca size={58} color={C.blanco} />
				</Sube>
			</AbsoluteFill>
			<div style={{position: 'absolute', bottom: 70, left: 0, right: 0, textAlign: 'center', fontSize: 24, opacity: 0.6}}>{AVISO_LEGAL}</div>
		</Fondo>
	);
};

export const VideoPublicidad: React.FC = () => {
	const orden: [keyof typeof ESCENAS, React.FC][] = [
		['gancho', Gancho],
		['dolor', Dolor],
		['revelacion', Revelacion],
		['demo', Demo],
		['fraude', Fraude],
		['beneficios', Beneficios],
		['cierre', Cierre],
	];
	let desde = 0;
	return (
		<AbsoluteFill style={{background: C.fondo}}>
			{orden.map(([nombre, Escena]) => {
				const s = (
					<Sequence key={nombre} from={desde} durationInFrames={ESCENAS[nombre]} name={nombre}>
						<Escena />
					</Sequence>
				);
				desde += ESCENAS[nombre];
				return s;
			})}
		</AbsoluteFill>
	);
};

