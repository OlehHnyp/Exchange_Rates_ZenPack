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
        let numberArray = strNumber.split(".")
        let leadingNumber = numberArray.shift()
        let trailingNumber = numberArray.join()
        let reverseStrNumber = reverseString(leadingNumber)
        let array = reverseStrNumber.match(regex)
        if(array){
            let splitedReverseStrNumber = array.join(" ")
            let splitedStrNumber = reverseString(splitedReverseStrNumber)
            return splitedStrNumber + trailingNumber
        }
        return n
    }
});