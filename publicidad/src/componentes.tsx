import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, MARCA} from './config';
import {fontFamily} from './fuentes';
import {Alerta, Check, Logo} from './iconos';

/** Entrada con resorte que empieza en `retraso` frames. */
export const useEntrada = (retraso = 0, damping = 16) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return spring({frame: frame - retraso, fps, config: {damping, mass: 0.7}});
};

export const Fondo: React.FC<{children: React.ReactNode; oscuro?: boolean}> = ({children, oscuro}) => (
	<AbsoluteFill
		style={{
			fontFamily,
			color: oscuro ? C.blanco : C.tinta,
			background: oscuro
				? `radial-gradient(120% 80% at 50% 0%, #1E4FB8 0%, ${C.marcaOscura} 55%, #071736 100%)`
				: `radial-gradient(120% 70% at 50% 0%, #FFFFFF 0%, ${C.fondo} 60%, #E8EEF6 100%)`,
		}}
	>
		{children}
	</AbsoluteFill>
);

export const Spinner: React.FC<{size?: number; color?: string}> = ({size = 40, color = C.blanco}) => {
	const frame = useCurrentFrame();
	return (
		<svg width={size} height={size} viewBox="0 0 24 24" style={{transform: `rotate(${frame * 14}deg)`}}>
			<circle cx="12" cy="12" r="9" stroke={color} strokeOpacity=".3" strokeWidth="3" fill="none" />
			<path d="M12 3a9 9 0 019 9" stroke={color} strokeWidth="3" fill="none" strokeLinecap="round" />
		</svg>
	);
};

export const Marca: React.FC<{size?: number; color?: string}> = ({size = 64, color = C.tinta}) => (
	<div style={{display: 'flex', alignItems: 'center', gap: size * 0.3}}>
		<Logo size={size * 1.25} />
		<span style={{fontSize: size, fontWeight: 800, letterSpacing: -size * 0.03, color}}>{MARCA}</span>
	</div>
);

export type Estado = 'vacio' | 'cargando' | 'aprobado' | 'ya_usada';

const Campo: React.FC<{etiqueta: string; valor: string; cursor?: boolean; escala: number}> = ({etiqueta, valor, cursor, escala}) => {
	const frame = useCurrentFrame();
	const parpadeo = Math.floor(frame / 15) % 2 === 0;
	return (
		<div style={{flex: 1}}>
			<div style={{fontSize: 22 * escala, fontWeight: 600, color: C.tintaSuave, marginBottom: 10 * escala}}>{etiqueta}</div>
			<div
				style={{
					height: 84 * escala,
					border: `2px solid ${cursor ? C.marca : C.borde}`,
					boxShadow: cursor ? `0 0 0 ${5 * escala}px rgba(20,82,204,.12)` : 'none',
					borderRadius: 16 * escala,
					display: 'flex',
					alignItems: 'center',
					padding: `0 ${22 * escala}px`,
					fontSize: 36 * escala,
					fontWeight: 600,
					background: C.blanco,
					fontVariantNumeric: 'tabular-nums',
				}}
			>
				{valor}
				{cursor && <span style={{width: 3 * escala, height: 40 * escala, background: parpadeo ? C.marca : 'transparent', marginLeft: 4}} />}
			</div>
		</div>
	);
};

/** Maqueta de la pantalla del programa. Todo se controla por props para poder animarla. */
export const TarjetaApp: React.FC<{
	referencia: string;
	monto: string;
	foco?: 'ref' | 'monto' | null;
	estado: Estado;
	botonPresion?: number; // 0..1
	resultado?: number; // 0..1 aparición del resultado
	ancho?: number;
}> = ({referencia, monto, foco = null, estado, botonPresion = 0, resultado = 1, ancho = 900}) => {
	const e = ancho / 900;
	const cargando = estado === 'cargando';
	const res =
		estado === 'aprobado'
			? {bg: C.verdeFondo, fg: C.verde, titulo: 'Aprobado', detalle: 'Pago móvil recibido · Bs. 2.000,00 · Hoy 10:42', Icono: Check}
			: estado === 'ya_usada'
				? {bg: C.ambarFondo, fg: C.ambar, titulo: 'Esta referencia ya fue usada', detalle: 'Se aprobó hoy a las 10:42 por María', Icono: Alerta}
				: null;
	return (
		<div
			style={{
				width: ancho,
				background: C.blanco,
				borderRadius: 36 * e,
				boxShadow: '0 30px 80px rgba(11,31,58,.18), 0 4px 14px rgba(11,31,58,.06)',
				overflow: 'hidden',
				color: C.tinta,
			}}
		>
			<div style={{display: 'flex', alignItems: 'center', gap: 12 * e, padding: `${22 * e}px ${32 * e}px`, borderBottom: `1px solid ${C.borde}`}}>
				<Logo size={44 * e} />
				<div style={{fontSize: 28 * e, fontWeight: 700}}>{MARCA}</div>
				<div style={{marginLeft: 'auto', fontSize: 22 * e, color: C.tintaSuave, fontWeight: 500}}>cuenta ***1234</div>
			</div>
			<div style={{padding: 32 * e}}>
				<div style={{display: 'flex', gap: 20 * e}}>
					<Campo etiqueta="Referencia" valor={referencia} cursor={foco === 'ref'} escala={e} />
					<Campo etiqueta="Monto (Bs.)" valor={monto} cursor={foco === 'monto'} escala={e} />
				</div>
				<div
					style={{
						marginTop: 26 * e,
						height: 88 * e,
						borderRadius: 18 * e,
						background: C.marca,
						color: C.blanco,
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
						gap: 16 * e,
						fontSize: 34 * e,
						fontWeight: 700,
						transform: `scale(${1 - botonPresion * 0.04})`,
						opacity: cargando ? 0.85 : 1,
					}}
				>
					{cargando ? (
						<>
							<Spinner size={40 * e} /> Verificando…
						</>
					) : (
						'Verificar'
					)}
				</div>
				{res && (
					<div
						style={{
							marginTop: 26 * e,
							background: res.bg,
							color: res.fg,
							borderRadius: 22 * e,
							padding: `${26 * e}px ${28 * e}px`,
							display: 'flex',
							gap: 22 * e,
							alignItems: 'center',
							opacity: resultado,
							transform: `translateY(${(1 - resultado) * 30 * e}px) scale(${0.94 + resultado * 0.06})`,
						}}
					>
						<div
							style={{
								width: 76 * e,
								height: 76 * e,
								borderRadius: 999,
								background: res.fg,
								display: 'flex',
								alignItems: 'center',
								justifyContent: 'center',
								flexShrink: 0,
							}}
						>
							<res.Icono size={46 * e} color={C.blanco} grosor={3} />
						</div>
						<div>
							<div style={{fontSize: 40 * e, fontWeight: 800}}>{res.titulo}</div>
							<div style={{fontSize: 24 * e, fontWeight: 500, marginTop: 6 * e, color: C.tinta, opacity: 0.75}}>{res.detalle}</div>
						</div>
					</div>
				)}
			</div>
		</div>
	);
};

/** Texto que entra subiendo y aparece. */
export const Sube: React.FC<{retraso?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({retraso = 0, children, style}) => {
	const p = useEntrada(retraso);
	return (
		<div style={{opacity: p, transform: `translateY(${interpolate(p, [0, 1], [40, 0])}px)`, ...style}}>{children}</div>
	);
};

/** Salida suave al final de una escena. */
export const useSalida = (duracion: number, frames = 10) => {
	const frame = useCurrentFrame();
	return interpolate(frame, [duracion - frames, duracion], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
};
