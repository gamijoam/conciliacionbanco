import React from 'react';

type P = {size?: number; color?: string; grosor?: number};

export const Check: React.FC<P> = ({size = 48, color = 'currentColor', grosor = 3}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none">
		<path d="M5 12.5l4.5 4.5L19 7.5" stroke={color} strokeWidth={grosor} strokeLinecap="round" strokeLinejoin="round" />
	</svg>
);

export const Equis: React.FC<P> = ({size = 48, color = 'currentColor', grosor = 3}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none">
		<path d="M6 6l12 12M18 6L6 18" stroke={color} strokeWidth={grosor} strokeLinecap="round" />
	</svg>
);

export const Alerta: React.FC<P> = ({size = 48, color = 'currentColor', grosor = 2.4}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none">
		<path d="M12 3.5L2.8 19.5h18.4L12 3.5z" stroke={color} strokeWidth={grosor} strokeLinejoin="round" />
		<path d="M12 10v4.5" stroke={color} strokeWidth={grosor} strokeLinecap="round" />
		<circle cx="12" cy="17" r="1.2" fill={color} />
	</svg>
);

export const Candado: React.FC<P> = ({size = 48, color = 'currentColor', grosor = 2.2}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none">
		<rect x="4.5" y="10.5" width="15" height="10" rx="2.5" stroke={color} strokeWidth={grosor} />
		<path d="M8 10.5V7.5a4 4 0 018 0v3" stroke={color} strokeWidth={grosor} />
	</svg>
);

export const Personas: React.FC<P> = ({size = 48, color = 'currentColor', grosor = 2.2}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none">
		<circle cx="9" cy="8" r="3.5" stroke={color} strokeWidth={grosor} />
		<path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5" stroke={color} strokeWidth={grosor} strokeLinecap="round" />
		<path d="M16 4.8a3.5 3.5 0 010 6.4M18.5 14.8c1.6.8 2.6 2.5 3 5.2" stroke={color} strokeWidth={grosor} strokeLinecap="round" />
	</svg>
);

export const Lista: React.FC<P> = ({size = 48, color = 'currentColor', grosor = 2.2}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none">
		<rect x="4" y="3" width="16" height="18" rx="2.5" stroke={color} strokeWidth={grosor} />
		<path d="M8 8h8M8 12h8M8 16h5" stroke={color} strokeWidth={grosor} strokeLinecap="round" />
	</svg>
);

export const Reloj: React.FC<P & {angulo?: number}> = ({size = 48, color = 'currentColor', grosor = 2.2, angulo = 0}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none">
		<circle cx="12" cy="12" r="9" stroke={color} strokeWidth={grosor} />
		<path d="M12 12V7" stroke={color} strokeWidth={grosor} strokeLinecap="round" transform={`rotate(${angulo} 12 12)`} />
		<path d="M12 12l3 2" stroke={color} strokeWidth={grosor} strokeLinecap="round" />
	</svg>
);

export const Chat: React.FC<P> = ({size = 48, color = 'currentColor', grosor = 2.2}) => (
	<svg width={size} height={size} viewBox="0 0 24 24" fill="none">
		<path d="M4 18.5l1.2-3.6A8 8 0 1112 20a8 8 0 01-4.2-1.2L4 18.5z" stroke={color} strokeWidth={grosor} strokeLinejoin="round" />
	</svg>
);

export const Logo: React.FC<{size?: number}> = ({size = 120}) => (
	<svg width={size} height={size} viewBox="0 0 64 64">
		<defs>
			<linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
				<stop offset="0" stopColor="#2F6BFF" />
				<stop offset="1" stopColor="#0B2E73" />
			</linearGradient>
		</defs>
		<rect width="64" height="64" rx="16" fill="url(#lg)" />
		<path d="M20 21h24M20 30h14" stroke="#fff" strokeOpacity=".55" strokeWidth="4" strokeLinecap="round" />
		<circle cx="42" cy="42" r="11" fill="#12A150" />
		<path d="M37 42.3l3.4 3.4 6.4-6.6" stroke="#fff" strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
	</svg>
);
