"""
Advanced Subnetting & Network Planning Tool
Flask Backend - All subnetting logic and API endpoints
"""

from flask import Flask, render_template, request, jsonify, send_file
import ipaddress
import math
import csv
import io
import json

app = Flask(__name__)

# ─────────────────────────────────────────
#  Helper Utilities
# ─────────────────────────────────────────

def ip_to_binary(ip_str):
    """Convert an IP address string to its 32-bit binary representation."""
    parts = ip_str.split('.')
    return '.'.join(f'{int(p):08b}' for p in parts)

def get_ip_class(ip_str):
    """Identify the class of an IPv4 address."""
    first_octet = int(ip_str.split('.')[0])
    if 1 <= first_octet <= 126:
        return 'A'
    elif first_octet == 127:
        return 'Loopback'
    elif 128 <= first_octet <= 191:
        return 'B'
    elif 192 <= first_octet <= 223:
        return 'C'
    elif 224 <= first_octet <= 239:
        return 'D (Multicast)'
    elif 240 <= first_octet <= 255:
        return 'E (Reserved)'
    return 'Unknown'

def cidr_to_mask(cidr):
    """Convert CIDR prefix length to dotted-decimal subnet mask."""
    mask_int = (0xFFFFFFFF << (32 - int(cidr))) & 0xFFFFFFFF
    return '.'.join([str((mask_int >> (8 * i)) & 0xFF) for i in [3, 2, 1, 0]])

def mask_to_cidr(mask_str):
    """Convert dotted-decimal subnet mask to CIDR prefix length."""
    parts = mask_str.split('.')
    binary = ''.join(f'{int(p):08b}' for p in parts)
    return binary.count('1')

def validate_ip(ip_str):
    """Validate an IP address string."""
    try:
        ipaddress.IPv4Address(ip_str)
        return True
    except Exception:
        return False

def calculate_subnet_info(network_str):
    """
    Given a CIDR network string (e.g. '192.168.1.0/24'),
    return a dict with all subnet details.
    """
    net = ipaddress.IPv4Network(network_str, strict=False)
    total_hosts = net.num_addresses
    usable_hosts = max(total_hosts - 2, 0)

    hosts = list(net.hosts())
    first_usable = str(hosts[0]) if hosts else str(net.network_address)
    last_usable  = str(hosts[-1]) if hosts else str(net.broadcast_address)

    return {
        'network':        str(net.network_address),
        'cidr':           net.prefixlen,
        'subnet_mask':    str(net.netmask),
        'wildcard_mask':  str(net.hostmask),
        'broadcast':      str(net.broadcast_address),
        'first_usable':   first_usable,
        'last_usable':    last_usable,
        'total_hosts':    total_hosts,
        'usable_hosts':   usable_hosts,
        'ip_class':       get_ip_class(str(net.network_address)),
        'binary_network': ip_to_binary(str(net.network_address)),
        'binary_mask':    ip_to_binary(str(net.netmask)),
        'is_private':     net.is_private,
    }

# ─────────────────────────────────────────
#  Page Routes
# ─────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

@app.route('/generator')
def generator():
    return render_template('generator.html')

@app.route('/vlsm')
def vlsm():
    return render_template('vlsm.html')

@app.route('/tools')
def tools():
    return render_template('tools.html')

@app.route('/simulation')
def simulation():
    return render_template('simulation.html')

# ─────────────────────────────────────────
#  API Endpoints
# ─────────────────────────────────────────

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    """Subnet Calculator API"""
    data = request.get_json()
    try:
        network_str = f"{data['ip']}/{data['cidr']}"
        info = calculate_subnet_info(network_str)
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Subnet Generator API - split a network by count or host requirement."""
    data = request.get_json()
    try:
        base_net = ipaddress.IPv4Network(f"{data['network']}", strict=False)
        mode      = data.get('mode', 'subnets')   # 'subnets' | 'hosts'
        count     = int(data.get('count', 2))

        if mode == 'subnets':
            # Calculate required prefix length
            bits_needed = math.ceil(math.log2(count))
            new_prefix  = base_net.prefixlen + bits_needed
        else:  # hosts per subnet
            bits_needed = math.ceil(math.log2(count + 2))
            new_prefix  = 32 - bits_needed

        if new_prefix > 32:
            return jsonify({'success': False, 'error': 'Prefix length exceeds /32'})

        subnets = list(base_net.subnets(new_prefix=new_prefix))
        result  = []
        for sn in subnets:
            hosts   = list(sn.hosts())
            result.append({
                'network':      str(sn.network_address),
                'cidr':         sn.prefixlen,
                'subnet_mask':  str(sn.netmask),
                'first_usable': str(hosts[0])  if hosts else str(sn.network_address),
                'last_usable':  str(hosts[-1]) if hosts else str(sn.broadcast_address),
                'broadcast':    str(sn.broadcast_address),
                'usable_hosts': max(sn.num_addresses - 2, 0),
                'total_hosts':  sn.num_addresses,
            })

        return jsonify({
            'success': True,
            'data': result,
            'new_prefix': new_prefix,
            'total_subnets': len(result),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/vlsm', methods=['POST'])
def api_vlsm():
    """VLSM Calculator - allocate subnets optimally for departments."""
    data = request.get_json()
    try:
        base_network = ipaddress.IPv4Network(data['network'], strict=False)
        departments  = sorted(data['departments'], key=lambda d: d['hosts'], reverse=True)

        allocations   = []
        current_start = base_network.network_address

        for dept in departments:
            required_hosts  = dept['hosts']
            bits_needed     = math.ceil(math.log2(required_hosts + 2))
            prefix          = 32 - bits_needed

            # Find the next subnet starting at current_start with correct prefix
            candidate = ipaddress.IPv4Network(f"{current_start}/{prefix}", strict=False)

            # Make sure it fits in the base network
            if not candidate.subnet_of(base_network):
                return jsonify({'success': False, 'error': f"Not enough space for department: {dept['name']}"})

            hosts = list(candidate.hosts())
            efficiency = (required_hosts / max(candidate.num_addresses - 2, 1)) * 100

            allocations.append({
                'department':   dept['name'],
                'required':     required_hosts,
                'network':      str(candidate.network_address),
                'cidr':         prefix,
                'subnet_mask':  str(candidate.netmask),
                'first_usable': str(hosts[0])  if hosts else '',
                'last_usable':  str(hosts[-1]) if hosts else '',
                'broadcast':    str(candidate.broadcast_address),
                'usable_hosts': max(candidate.num_addresses - 2, 0),
                'total_hosts':  candidate.num_addresses,
                'wasted_ips':   max(candidate.num_addresses - 2, 0) - required_hosts,
                'efficiency':   round(efficiency, 1),
            })

            # Advance past this subnet
            next_addr = int(candidate.broadcast_address) + 1
            if next_addr > int(base_network.broadcast_address):
                break
            current_start = ipaddress.IPv4Address(next_addr)

        return jsonify({'success': True, 'data': allocations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/tools/cidr_to_mask', methods=['POST'])
def api_cidr_to_mask():
    data = request.get_json()
    try:
        mask = cidr_to_mask(data['cidr'])
        return jsonify({'success': True, 'mask': mask})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/tools/mask_to_cidr', methods=['POST'])
def api_mask_to_cidr():
    data = request.get_json()
    try:
        cidr = mask_to_cidr(data['mask'])
        return jsonify({'success': True, 'cidr': cidr})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/tools/validate_ip', methods=['POST'])
def api_validate_ip():
    data = request.get_json()
    ip   = data.get('ip', '')
    valid = validate_ip(ip)
    result = {'valid': valid, 'ip': ip}
    if valid:
        result['class'] = get_ip_class(ip)
        result['binary'] = ip_to_binary(ip)
        addr = ipaddress.IPv4Address(ip)
        result['is_private']   = addr.is_private
        result['is_loopback']  = addr.is_loopback
        result['is_multicast'] = addr.is_multicast
    return jsonify({'success': True, 'data': result})


@app.route('/api/simulation', methods=['POST'])
def api_simulation():
    """Generate step-by-step subnetting simulation data."""
    data = request.get_json()
    try:
        ip   = data['ip']
        cidr = int(data['cidr'])

        ip_bin    = ip_to_binary(ip).replace('.', '')
        mask_bin  = '1' * cidr + '0' * (32 - cidr)
        mask_str  = cidr_to_mask(cidr)
        mask_bin_dotted = ip_to_binary(mask_str).replace('.', '')

        network_bin = ''.join('1' if (b1 == '1' and b2 == '1') else '0'
                              for b1, b2 in zip(ip_bin, mask_bin))
        broadcast_bin = network_bin[:cidr] + '1' * (32 - cidr)

        def bin_to_ip(b):
            return '.'.join(str(int(b[i:i+8], 2)) for i in range(0, 32, 8))

        network_ip   = bin_to_ip(network_bin)
        broadcast_ip = bin_to_ip(broadcast_bin)
        first_host   = bin_to_ip(network_bin[:31] + ('1' if network_bin[31] == '0' else '1'))

        # Proper first/last host
        net_int   = int(network_bin, 2)
        first_int = net_int + 1
        last_int  = int(broadcast_bin, 2) - 1

        first_host_ip = bin_to_ip(f'{first_int:032b}') if first_int <= last_int else network_ip
        last_host_ip  = bin_to_ip(f'{last_int:032b}')  if first_int <= last_int else broadcast_ip

        steps = [
            {
                'step': 1,
                'title': 'Convert IP to Binary',
                'description': f'Convert each octet of {ip} to 8-bit binary.',
                'ip_binary': ip_to_binary(ip),
                'ip_binary_flat': ip_bin,
                'cidr': cidr,
            },
            {
                'step': 2,
                'title': 'Apply Subnet Mask',
                'description': f'The /{cidr} mask means first {cidr} bits are network bits, remaining {32-cidr} are host bits.',
                'mask_binary': ip_to_binary(mask_str),
                'mask_binary_flat': mask_bin_dotted,
                'cidr': cidr,
            },
            {
                'step': 3,
                'title': 'Identify Network Bits vs Host Bits',
                'description': f'AND the IP with subnet mask to get the Network ID. First {cidr} bits = Network portion, last {32-cidr} bits = Host portion.',
                'ip_binary_flat': ip_bin,
                'mask_binary_flat': mask_bin_dotted,
                'network_binary_flat': network_bin,
                'cidr': cidr,
            },
            {
                'step': 4,
                'title': 'Calculate Network Address',
                'description': 'Set all host bits to 0 to get the Network Address.',
                'network_binary_flat': network_bin,
                'network_ip': network_ip,
                'cidr': cidr,
            },
            {
                'step': 5,
                'title': 'Calculate Broadcast Address',
                'description': 'Set all host bits to 1 to get the Broadcast Address.',
                'broadcast_binary_flat': broadcast_bin,
                'broadcast_ip': broadcast_ip,
                'cidr': cidr,
            },
            {
                'step': 6,
                'title': 'Calculate Host Range',
                'description': 'First usable host = Network + 1. Last usable host = Broadcast - 1.',
                'first_host': first_host_ip,
                'last_host': last_host_ip,
                'total_hosts': 2 ** (32 - cidr),
                'usable_hosts': max(2 ** (32 - cidr) - 2, 0),
                'cidr': cidr,
            },
        ]

        return jsonify({'success': True, 'steps': steps, 'total_steps': len(steps)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/planner', methods=['POST'])
def api_planner():
    """Smart Network Planner - suggest optimal subnetting."""
    data = request.get_json()
    try:
        total_hosts   = int(data['total_hosts'])
        num_subnets   = int(data['num_subnets'])
        base_net_str  = data.get('base_network', '10.0.0.0/8')

        base_net = ipaddress.IPv4Network(base_net_str, strict=False)
        hosts_per_subnet = math.ceil(total_hosts / num_subnets)
        bits_for_hosts   = math.ceil(math.log2(hosts_per_subnet + 2))
        new_prefix       = 32 - bits_for_hosts

        suggestions = []
        for prefix in range(max(new_prefix - 2, base_net.prefixlen + 1), min(new_prefix + 3, 33)):
            hosts_per = max(2 ** (32 - prefix) - 2, 0)
            efficiency = (hosts_per_subnet / hosts_per * 100) if hosts_per > 0 else 0
            waste      = hosts_per - hosts_per_subnet
            suggestions.append({
                'prefix':          prefix,
                'subnet_mask':     cidr_to_mask(prefix),
                'hosts_per_subnet': hosts_per,
                'efficiency':      round(min(efficiency, 100), 1),
                'wasted_per_subnet': max(waste, 0),
                'recommended':     (prefix == new_prefix),
            })

        return jsonify({'success': True, 'suggestions': suggestions, 'recommended_prefix': new_prefix})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/export', methods=['POST'])
def api_export():
    """Export subnet data as CSV or TXT."""
    data   = request.get_json()
    fmt    = data.get('format', 'csv')
    rows   = data.get('data', [])
    title  = data.get('title', 'subnet_results')

    if fmt == 'csv':
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={title}.csv'}
        )
    else:  # txt
        lines = []
        for row in rows:
            for k, v in row.items():
                lines.append(f'{k}: {v}')
            lines.append('-' * 40)
        return app.response_class(
            '\n'.join(lines),
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename={title}.txt'}
        )


if __name__ == '__main__':
    app.run(debug=True, port=5000)
