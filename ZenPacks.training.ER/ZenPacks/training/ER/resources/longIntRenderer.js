Ext.apply(Zenoss.render, {
    longIntegerRenderer: function(n) {
        function reverseString(str) {
            let result = ""
            for(let i of str){
                result = i + result
            }
            return result
        }

        const regex = /\d{1,3}/g
        let strNumber = String(n)
        let reverseStrNumber = reverseString(strNumber)
        let array = reverseStrNumber.match(regexp)
        let splitedReverseStrNumber = array.reduce((a, b)=>a + " " + b)
        let splitedStrNumber = reverseString(splitedReverseStrNumber)

        return splitedStrNumber
    }
});